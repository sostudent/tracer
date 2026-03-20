# tracer
tracer for running executables in linux
# requirements
```
python3
python-ptrace (it can be installed with pip3 install python-ptrace)
```
# simple c program
```
#include <stdio.h>

int main(void){
	printf("sleeping\n");
	sleep(1);
	int pid1 = fork();
	printf("%d\n", pid1);
}
```

# output example for that simple c program
```
--- Trace activ pe PID 72446 ---
[WRITE] PID 72446 (FD 1): b'sleeping\n'
sleeping
[FORK] PID 72447 (CHILD) -> Rezultat: 0
0
[WRITE] PID 72447 (FD 1): b'0\n'
[EXIT] PID 72447 s-a terminat.
[FORK] PID 72446 (PARENT) -> Rezultat: 72447
72447
[WRITE] PID 72446 (FD 1): b'72447\n'
[EXIT] PID 72446 s-a terminat.
--- Trace finalizat ---
```
