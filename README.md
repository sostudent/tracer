# tracer

It only parses the output from strace

# install and run instuctions
```
gcc ex_1.c
strace -f -tt -e trace=write,read,fork,clone,execve -s 100 -o output.txt ./a.out
strace -f -tt -e trace=write,read,fork,clone,execve,pipe,pipe2,open,close -s 100 -o output.txt ./a.out parametru
cat output.txt | python3 parse_strace_v3.py

strace -f -tt -e trace=write,read,fork,clone,execve,pipe,pipe2,open,close,pause,signal,rt_sigaction,wait4,alarm -s 100 -o output.txt ./a.out parametru
cat output.txt | python3 parse_strace_v4.py

strace -f -tt -e trace=all -s 100 -o output.txt ./a.out parametru
cat output.txt | python3 parse_strace_v4.py

(not working properly)
stdbuf -oL strace -f -tt -e trace=write,read,fork,clone,openat,exit_group,execve,pipe,pipe2,open,close ./a.out parametru 2>&1 | python3 parse_strace_v3.py
```

ISO to install linux in a virtual machine: 
 - (x86/windows/linux) "https://mirrors.nxthost.com/rocky/9/isos/x86_64/Rocky-9.7-x86_64-minimal.iso"
 - (arm/mac) "https://mirrors.nxthost.com/rocky/9/isos/aarch64/Rocky-9.7-aarch64-minimal.iso"

What to run in the new installed virtual machine
```bash
# (hostname -I will show the local IP for the new virtual machine so that you can connect directly with ssh to it)
hostname -I
# (after getting the IP, connect with ssh to the new virtual machine for easier access)
ssh IP_OF_THE_VIRTUAL_MACHINE
# (optional to install python pip)
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py 

# (optional to install vim)
dnf install vim
(it will install gcc, it can also be installed separatelly)
dnf groupinstall "Development Tools"
```

# simple c program
```c
#include <stdio.h>
#include <unistd.h>

int main(void){
	printf("sleeping\n");
	sleep(1);
	int pid1 = fork();
	printf("%d\n", pid1);
}
```
# output example from v2 for the tracer (it has collors + alignemnt, it looks better in the terminal)
```
--- Parser activ (Aștept date...) ---
[PID MAIN] [READ ] Data: \177ELF\2\1\1\0\0\0\0\0\0\0\0\0\3\0\267\0\1\0\0\0p
[PID MAIN] [READ ] Data: \177ELF\2\1\1\3\0\0\0\0\0\0\0\0\3\0\267\0\1\0\0\00
[PID MAIN] [WRITE] Text: sleeping\n
[PID MAIN] [FORK ] Părintele a creat copilul: 43245
 └─ [PID 43245] [WRITE] Text: 0\n
 └─ [PID 43245] [EXIT ] Proces finalizat.
[PID MAIN] [WRITE] Text: 43245\n
[PID MAIN] [EXIT ] Proces finalizat.
```

# intrebari
- ce afiseaza daca se scoate \n de la printf
- cum se poate ca sa afiseze numarul mai mare inaintea numarului mic

