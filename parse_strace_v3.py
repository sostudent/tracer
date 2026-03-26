import sys, re

# Configurare Culori
RED_BG = '\033[41m\033[37m'
COLORS = ['\033[96m', '\033[92m', '\033[93m', '\033[95m', '\033[94m', '\033[91m']
RESET = '\033[0m'

pid_colors = {}
pid_depth = {}
unfinished_calls = {}
# Mapare globală a descriptorilor cunoscuți
fd_map = {
    "0": "STDIN",
    "1": "STDOUT",
    "2": "STDERR"
}
color_idx = 0

def log_event(pid, tag, message, is_error=False):
    global color_idx
    if pid not in pid_colors:
        pid_colors[pid] = COLORS[color_idx % len(COLORS)]
        color_idx += 1
    
    color = pid_colors[pid]
    depth = pid_depth.get(pid, 0)
    indent = "  " * (depth - 1) + " └─ " if depth > 0 else ""
    
    err_prefix = f"{RED_BG} [ERROR] {RESET} " if is_error else ""
    print(f"{color}{indent}[PID {pid}] [{tag:<5}] {err_prefix}{message}{RESET}", flush=True)

def clean_data(text):
    # Extrage textul dintre ghilimele
    match = re.search(r'"(.*?)"', text)
    if match:
        return match.group(1) if match.group(1) else "[Empty]"
    return "[Binary/Large]"

def main():
    print("--- Parser activ (Pipe Tracking Fix) ---", flush=True)
    
    for line in sys.stdin:
        line = line.strip()
        if not line: continue

        # Identificare PID și conținut
        main_match = re.match(r'^(\d+)\s+[\d:.]+\s+(.*)', line)
        if not main_match: continue
        pid, rest = main_match.groups()

        # Reconstrucție apeluri întrerupte
        if "<unfinished ...>" in rest:
            unfinished_calls[pid] = rest.replace("<unfinished ...>", "").strip()
            continue
        if "resumed>" in rest:
            prev = unfinished_calls.pop(pid, "")
            res_part = re.search(r'resumed>(.*)', rest)
            rest = prev + (res_part.group(1) if res_part else "")

        # Status eroare
        is_error = " = -1 " in rest
        error_info = ""
        if is_error:
            err_search = re.search(r'=\s+-1\s+(.*)', rest)
            error_info = f" -> FAILED: {err_search.group(1)}" if err_search else " -> FAILED"

        # --- 1. PIPE Detection ---
        if "pipe" in rest:
            fds = re.search(r'\[(\d+),\s*(\d+)\]', rest)
            if fds:
                r, w = fds.groups()
                fd_map[r] = "PIPE_RD"
                fd_map[w] = "PIPE_WR"
                log_event(pid, "PIPE", f"New Pipe: {r}(R) <-> {w}(W)")
            continue

        # --- 2. OPEN Detection ---
        if "open" in rest and "(" in rest:
            path = re.search(r'"(.*?)"', rest)
            res = re.search(r'=\s+(\d+)', rest)
            if path and res and not is_error:
                fd_num = res.group(1)
                fd_map[fd_num] = f"FILE:{path.group(1).split('/')[-1]}"
                log_event(pid, "OPEN", f"File: {path.group(1)} -> FD {fd_num}")
            elif path:
                log_event(pid, "OPEN", f"File: {path.group(1)}{error_info}", is_error)
            continue

        # --- 3. READ / WRITE Detection ---
        rw_match = re.match(r'^(read|write)\((\d+),', rest)
        if rw_match:
            syscall, fd = rw_match.groups()
            # Căutăm tipul de FD în maparea noastră
            fd_type = fd_map.get(fd, "UNK")
            
            # Filtrăm zgomotul de sistem (ELF)
            if "\\177ELF" not in rest:
                msg = f"[FD {fd} ({fd_type})] {clean_data(rest)}{error_info}"
                log_event(pid, syscall.upper(), msg, is_error)
            continue

        # --- 4. CLOSE Detection ---
        if "close(" in rest:
            fd_search = re.search(r'close\((\d+)\)', rest)
            if fd_search:
                fd_num = fd_search.group(1)
                fd_type = fd_map.get(fd_num, "UNK")
                log_event(pid, "CLOSE", f"FD {fd_num} ({fd_type}){error_info}", is_error)
                # NOTĂ: Nu ștergem din fd_map aici pentru că alte procese/copii
                # pot folosi încă aceleași numere de FD pentru aceleași pipe-uri.
            continue

        # --- 5. FORK / EXEC / EXIT ---
        if "clone(" in rest or "fork(" in rest:
            res = re.search(r'=\s+(\d+)', rest)
            if res:
                child = res.group(1)
                pid_depth[child] = pid_depth.get(pid, 0) + 1
                log_event(pid, "FORK", f"Child: {child}")
        elif "execve(" in rest:
            cmd = re.search(r'execve\("(.*?)",\s*\["(.*?)"', rest)
            if cmd: log_event(pid, "EXEC", f"{cmd.group(2)} ({cmd.group(1)})")
        elif "exited" in rest or "exit_group" in rest:
            log_event(pid, "EXIT", "Done.")

if __name__ == "__main__":
    main()
