import sys, os, subprocess, re, argparse

# --- CULORI PENTRU TERMINAL ---
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'

pipe_read_fds = set()
pipe_write_fds = set()

def compile_code(source_file):
    print(f"{CYAN}[*] Compilare {source_file}...{RESET}")
    binary = "./test_exec"
    result = subprocess.run(["gcc", source_file, "-o", binary], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"{RED}[EROARE FATALĂ] Compilarea a eșuat!{RESET}\n{result.stderr}")
        sys.exit(1)
    return binary

def run_strace(binary):
    print(f"{CYAN}[*] Rulare sub strace (interceptare syscalls, semnale, pipes)...{RESET}")
    strace_out = "strace_output.txt"
    # Folosim -s 2000 pentru a preveni trunchierea textelor lungi
    cmd = ["strace", "-f", "-s", "2000", "-e", "trace=all", "-o", strace_out, binary]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8)
    except subprocess.TimeoutExpired:
        print(f"\n{RED}[EROARE FATALĂ] Programul a depășit timpul limită! Posibilă buclă infinită.{RESET}")
        subprocess.run(["pkill", "-9", "-f", "test_exec"], stderr=subprocess.DEVNULL)
        sys.exit(1)
    return strace_out

def parse_strace(strace_out):
    processes = {}
    unfinished = {}
    main_pid = None
    event_counter = 0
    global pipe_read_fds, pipe_write_fds
    pipe_read_fds.clear()
    pipe_write_fds.clear()

    with open(strace_out, 'r') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            
            pid_match = re.match(r'^(\d+)\s+(.*)', line)
            if not pid_match: continue
            pid = int(pid_match.group(1))
            rest = pid_match.group(2)
            
            if main_pid is None: main_pid = pid
            if pid not in processes:
                processes[pid] = {'calls': [], 'children': []}

            if "<unfinished" in rest:
                unfinished[pid] = rest.replace("<unfinished ...>", "").strip()
                continue
            if "resumed>" in rest:
                prev = unfinished.pop(pid, "")
                res_part = re.search(r'resumed>\s*(.*)', rest)
                rest = prev + (res_part.group(1) if res_part else "")

            if rest.startswith("--- SIG"):
                sig_match = re.search(r'---\s+(SIG[A-Z0-9_]+)', rest)
                if sig_match:
                    event_counter += 1
                    processes[pid]['calls'].append({
                        'event_id': event_counter,
                        'type': 'SIGNAL_RECV',
                        'signal': sig_match.group(1),
                        'raw': rest
                    })
                continue

            sys_match = re.match(r'^([a-zA-Z0-9_]+)\((.*)', rest)
            if sys_match:
                event_counter += 1
                syscall = sys_match.group(1)
                args_and_res = sys_match.group(2)
                processes[pid]['calls'].append({
                    'event_id': event_counter,
                    'type': 'SYSCALL',
                    'syscall': syscall,
                    'raw': args_and_res
                })
                
                if syscall in ('clone', 'fork', 'vfork'):
                    res_match = re.search(r'=\s+(\d+)', args_and_res)
                    if res_match:
                        processes[pid]['children'].append(int(res_match.group(1)))
                
                elif syscall in ('pipe', 'pipe2'):
                    res_match = re.search(r'=\s+0', args_and_res)
                    if res_match:
                        fds = re.findall(r'\d+', args_and_res.split(')')[0])
                        if len(fds) >= 2:
                            pipe_read_fds.add(fds[0])
                            pipe_write_fds.add(fds[1])

    return processes, main_pid

def check_pid_written(processes, writer_pid, expected_val, other_pid=None, target='stdout', after_signal=None):
    if writer_pid not in processes: return False, False
    
    clone_event_id = -1
    if other_pid and other_pid in processes:
        for c in processes[other_pid]['calls']:
            if c.get('type') == 'SYSCALL' and c.get('syscall') in ('clone', 'fork', 'vfork'):
                clone_event_id = c['event_id']
                break
                
    other_writes_after_clone = []
    if other_pid and other_pid in processes:
        for c in processes[other_pid]['calls']:
            if c.get('type') == 'SYSCALL' and c.get('syscall') in ('write', 'writev') and c['event_id'] > clone_event_id:
                other_writes_after_clone.append(c['raw'])
                
    is_found = False
    is_duplicate = False
    found_signal = False if after_signal else True
    
    for call in processes[writer_pid]['calls']:
        # Fix pentru TypeError: Verificam in siguranta daca after_signal e setat si se afla in text
        if call.get('type') == 'SIGNAL_RECV':
            if after_signal and after_signal in call.get('signal', ''):
                found_signal = True
            continue

        if found_signal and call.get('type') == 'SYSCALL' and call.get('syscall') in ('write', 'writev'):
            fd_match = re.match(r'^(\d+),', call['raw'])
            if not fd_match: continue
            fd = fd_match.group(1)
            
            if target == 'stdout' and fd not in ('1', '2'): continue
            
            if re.search(r'\b' + str(expected_val) + r'\b', call['raw']):
            	# if str(expected_val) in call['raw']:
                if other_pid and call['raw'] in other_writes_after_clone:
                    is_duplicate = True
                else:
                    is_found = True
                    
    return is_found, is_duplicate

def has_written_pid(processes, writer_pid, expected_val, target='stdout', after_signal=None):
    found, _ = check_pid_written(processes, writer_pid, expected_val, target=target, after_signal=after_signal)
    return found

def has_sent_signal(processes, sender_pid, target_pid, signal_name):
    if sender_pid not in processes: return False
    for call in processes[sender_pid]['calls']:
        if call.get('type') == 'SYSCALL' and call.get('syscall') in ('kill', 'tgkill') and str(target_pid) in call['raw'] and signal_name in call['raw']:
            return True
    return False

# NOU: Verifica doar daca s-a folosit efectiv țeava (Pipe) - Rezolvă problema datelor binare!
def has_used_pipe(processes, pid, direction):
    if pid not in processes: return False
    for call in processes[pid]['calls']:
        if call.get('type') == 'SYSCALL':
            if direction == 'write' and call.get('syscall') in ('write', 'writev'):
                fd_match = re.match(r'^(\d+),', call['raw'])
                if fd_match and fd_match.group(1) in pipe_write_fds:
                    return True
            if direction == 'read' and call.get('syscall') == 'read':
                fd_match = re.match(r'^(\d+),', call['raw'])
                if fd_match and fd_match.group(1) in pipe_read_fds:
                    return True
    return False


# ================= EVALUATORI SPECIFICI =================

def eval_level_0(processes, main_pid):
    errors = []
    if not processes[main_pid]['children']: return ["P1 nu a creat P2 (niciun fork gasit)."]
    p2 = processes[main_pid]['children'][0]
    
    is_found, is_dup = check_pid_written(processes, p2, main_pid, other_pid=main_pid, target='stdout')
    
    if not is_found:
        if is_dup:
            errors.append(f"P2 a afisat PID-ul {main_pid}, dar din greseala de buffer (lipsa \\n inainte de fork).")
        else:
            errors.append(f"P2 (PID {p2}) NU a afisat PID-ul lui P1 (PID {main_pid}).")
    return errors

def eval_level_1(processes, main_pid):
    errors = []
    if not processes[main_pid]['children']: return ["P1 nu a creat P2."]
    p2 = processes[main_pid]['children'][0]
    
    if p2 not in processes or not processes[p2]['children']: return ["P2 nu a creat P3."]
    p3 = processes[p2]['children'][0]
    
    found_p1, _ = check_pid_written(processes, p3, main_pid, other_pid=main_pid, target='stdout')
    if not found_p1: errors.append(f"P3 (PID {p3}) NU a afisat PID-ul lui P1 (PID {main_pid}).")
        
    found_p2, _ = check_pid_written(processes, p3, p2, other_pid=p2, target='stdout')
    if not found_p2: errors.append(f"P3 (PID {p3}) NU a afisat PID-ul lui P2 (PID {p2}).")
        
    return errors

def eval_level_2(processes, main_pid):
    errors = []
    if not processes[main_pid]['children']: return ["P1 nu a creat P2."]
    p2 = processes[main_pid]['children'][0]
    
    if not has_sent_signal(processes, p2, main_pid, 'SIGALRM'):
        errors.append(f"P2 (PID {p2}) nu a trimis kill() cu SIGALRM catre P1.")
        
    if not has_written_pid(processes, main_pid, p2, target='stdout', after_signal='SIGALRM'):
        errors.append(f"P1 (PID {main_pid}) NU a afisat PID-ul lui P2 ({p2}) DUPA ce a primit SIGALRM.")
    return errors

def eval_level_3(processes, main_pid):
    errors = []
    if not processes[main_pid]['children']: return ["P1 nu a creat P2."]
    p2 = processes[main_pid]['children'][0]
    
    if p2 not in processes or not processes[p2]['children']: return ["P2 nu a creat P3."]
    p3 = processes[p2]['children'][0]
    
    sent_sigusr = has_sent_signal(processes, p3, main_pid, 'SIGUSR1') or has_sent_signal(processes, p3, main_pid, 'SIGUSR2')
    if not sent_sigusr:
        errors.append(f"P3 (PID {p3}) nu a trimis SIGUSR1/SIGUSR2 catre P1.")
        
    if not has_written_pid(processes, main_pid, p3, target='stdout', after_signal='SIGUSR'):
        errors.append(f"P1 (PID {main_pid}) NU a afisat PID-ul lui P3 ({p3}) DUPA ce a primit SIGUSR.")
    return errors

def eval_level_4(processes, main_pid):
    errors = []
    if not pipe_read_fds: return ["Nu a fost detectat niciun apel la pipe()."]
    
    if not processes[main_pid]['children']: return ["P1 nu a creat P2."]
    p2 = processes[main_pid]['children'][0]
    
    if not has_used_pipe(processes, p2, 'write'):
        errors.append(f"P2 (PID {p2}) NU a scris date in pipe.")
        
    if not has_used_pipe(processes, main_pid, 'read'):
        errors.append(f"P1 (PID {main_pid}) nu a citit date din pipe.")
        
    if not has_written_pid(processes, main_pid, main_pid, target='stdout'):
        errors.append(f"P1 (PID {main_pid}) NU a afisat la stdout PID-ul sau (care a fost adus prin pipe).")
        
    return errors

def eval_level_5(processes, main_pid):
    errors = []
    if not pipe_read_fds: return ["Nu a fost detectat niciun apel la pipe()."]
    
    if not processes[main_pid]['children']: return ["P1 nu a creat P2."]
    p2 = processes[main_pid]['children'][0]
    
    if p2 not in processes or not processes[p2]['children']: return ["P2 nu a creat P3."]
    p3 = processes[p2]['children'][0]
    
    if not has_used_pipe(processes, p3, 'write'):
        errors.append(f"P3 (PID {p3}) NU a scris date in pipe.")
        
    if not has_used_pipe(processes, main_pid, 'read'):
        errors.append(f"P1 (PID {main_pid}) nu a citit din pipe.")
        
    if not has_written_pid(processes, main_pid, main_pid, target='stdout'):
        errors.append(f"P1 (PID {main_pid}) NU a afisat la stdout PID-ul sau (adus prin pipe).")
        
    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--level", required=True, choices=["0", "1", "2", "3", "4", "5"])
    parser.add_argument("source")
    args = parser.parse_args()

    binary = compile_code(args.source)
    strace_out = run_strace(binary)
    processes, main_pid = parse_strace(strace_out)

    print(f"\n{CYAN}[*] Evaluare Solutie - Nivelul {args.level}{RESET}")
    print(f"    PID Principal identificat: {main_pid}")

    eval_func = globals()[f"eval_level_{args.level}"]
    errors = eval_func(processes, main_pid)

    if os.path.exists("test_exec"): os.remove("test_exec")
    if os.path.exists("strace_output.txt"): os.remove("strace_output.txt")

    if not errors:
        print(f"\n{GREEN}[+] IMPLEMENTARE CORECTA!{RESET}")
        sys.exit(0)
    else:
        print(f"\n{RED}[-] IMPLEMENTARE GRESITA.{RESET}")
        for err in errors: print(f"    - {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()
