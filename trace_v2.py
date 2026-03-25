import os, sys, struct, time
from ptrace.debugger import PtraceDebugger
from ptrace.binding.func import (PTRACE_O_TRACESYSGOOD, PTRACE_O_TRACEFORK, 
                                 PTRACE_O_TRACECLONE, PTRACE_O_TRACEEXEC)
from ptrace.binding import ptrace_traceme

# --- UI Formatting Setup ---
COLORS = [
    '\033[96m', # Cyan
    '\033[92m', # Green
    '\033[93m', # Yellow
    '\033[95m', # Magenta
    '\033[94m', # Blue
    '\033[91m', # Red
]
RESET_COLOR = '\033[0m'

syscall_state = {}
pid_colors = {}
pid_depth = {}
color_idx = 0

def log_event(pid, tag, message):
    """Helper function to format and print colored, indented trace logs."""
    global color_idx
    
    # Assign a unique color to this PID if it doesn't have one
    if pid not in pid_colors:
        pid_colors[pid] = COLORS[color_idx % len(COLORS)]
        color_idx += 1
        
    color = pid_colors[pid]
    depth = pid_depth.get(pid, 0)
    
    # Create the tree indentation (e.g., "   │   └─ ")
    indent = ""
    if depth > 0:
        indent = "  " * (depth - 1) + " └─ "
        
    # Print the formatted line
    print(f"{color}{indent}[PID {pid}] [{tag:<5}] {message}{RESET_COLOR}")
# ---------------------------

def trace_program(executable_path, args):
    debugger = PtraceDebugger()
    pid_parent = os.fork()
    
    if pid_parent == 0:
        ptrace_traceme()
        os.execv(executable_path, [executable_path] + args)
        sys.exit(1)

    time.sleep(0.2)
    process = debugger.addProcess(pid_parent, is_attached=True)
    options = (PTRACE_O_TRACESYSGOOD | PTRACE_O_TRACEFORK | 
               PTRACE_O_TRACECLONE | PTRACE_O_TRACEEXEC)
    process.setoptions(options)
    
    syscall_state[pid_parent] = 0
    pid_depth[pid_parent] = 0  # Parent is at depth 0 (root)
    
    process.syscall()

    print(f"--- Trace activ pe PID {pid_parent} ---")

    while debugger.list:
        try:
            event = debugger.waitProcessEvent()
            current_proc = event.process
            pid_curr = current_proc.pid
            
            if event.__class__.__name__ == "ProcessExit":
                log_event(pid_curr, "EXIT", "Procesul s-a terminat.")
                if pid_curr in syscall_state: del syscall_state[pid_curr]
                continue

            if event.__class__.__name__ == "NewProcessEvent":
                current_proc.setoptions(options)
                
                # Inherit tree depth from parent
                if hasattr(current_proc, 'parent') and current_proc.parent:
                    pid_depth[pid_curr] = pid_depth.get(current_proc.parent.pid, 0) + 1

                regs = current_proc.getregs()
                log_event(pid_curr, "FORK", f"(CHILD)  -> Rezultat: {regs.rax}")
                syscall_state[pid_curr] = 1 
                
                # Resume the child
                current_proc.syscall()
                
                # Resume the parent which was suspended during the fork creation
                if hasattr(current_proc, 'parent') and current_proc.parent:
                    current_proc.parent.syscall()
                continue

            # Alternăm între intrare (0) și ieșire (1)
            state = syscall_state.get(pid_curr, 0)
            syscall_state[pid_curr] = 1 - state

            # Procesăm DOAR la ieșire (state == 1)
            if syscall_state[pid_curr] == 1:
                regs = current_proc.getregs()
                sys_num = regs.orig_rax
                result = regs.rax

                if sys_num == 1: # write
                    data = current_proc.readBytes(regs.rsi, regs.rdx)
                    log_event(pid_curr, "WRITE", f"FD {regs.rdi}: {data!r}")
                
                elif sys_num == 0: # read
                    if 0 < result < 0xFFFFFFFFFFFFF000:
                        data = current_proc.readBytes(regs.rsi, result)
                        log_event(pid_curr, "READ", f"FD {regs.rdi}: {data!r}")

                elif sys_num in (56, 57): # fork/clone
                    if result < 0xFFFFFFFFFFFFF000:
                        log_event(pid_curr, "FORK", f"(PARENT) -> Rezultat: {result}")
                    else:
                        syscall_state[pid_curr] = 0

                elif sys_num in (22, 293): # pipe/pipe2
                    raw_fds = current_proc.readBytes(regs.rdi, 8)
                    fds = struct.unpack("ii", raw_fds)
                    log_event(pid_curr, "PIPE", f"FDs: {fds}")

            current_proc.syscall()

        except Exception as e:
            break

    debugger.quit()
    print("--- Trace finalizat ---")

if __name__ == "__main__":
    trace_program("./a.out",[])
