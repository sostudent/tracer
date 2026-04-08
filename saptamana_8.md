## probleme in fuctie de nivelul de cunostinte

# nivel -3
De compilat, rulat si de trimis din alt terminal un semnal cu comanda `kill -14 [PID process]`
```c
#include <setjmp.h>
#include <signal.h>
#include <fcntl.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
static void sig_alarm_custom(int);
int main(void)
{
        printf("PID %d\n", getpid());
        int n;
        char line[250];
        if (signal(SIGALRM, sig_alarm_custom) == SIG_ERR)
                printf("eroare sigalarm");
        alarm(10);
        if ((n=read(0, line, 250)) < 0)
                printf("eroare read");
        alarm(0);
        write(1, line, n);
        exit(0);
}
static void sig_alarm_custom(int sig)
{
        printf("semnal primit %d\n", sig);
        exit(1);
}
```

# nivel -2
De compilat, rulat si de trimis un semnal cu `kill -SIGUSR1 [PID process]`
```c
#include <stdio.h>
#include <signal.h>
#include <unistd.h>

void signal_handler(int sig, siginfo_t *info, void *context) {
    printf("Received signal %d from PID: %d\n", sig, info->si_pid);
}

int main() {
    struct sigaction sa;

    sa.sa_flags = SA_SIGINFO;        
    sa.sa_sigaction = signal_handler; 
    sigemptyset(&sa.sa_mask);

    if (sigaction(SIGUSR1, &sa, NULL) == -1) {
        printf("sigaction error");
        return 1;
    }

    printf("My PID is %d. Waiting for SIGUSR1...\n", getpid());
    while(1) pause();

    return 0;
}
```

# nivel -1
Problema 8.2 rezolvata, de compilat si rulat/testat.
```c
#include <setjmp.h>
#include <signal.h>
#include "hdr.h"
static void sig_alarm();
int main(void)
{
        int n;
        char line[MAXLINE];
        if (signal( SIGALRM, sig_alarm) == SIG_ERR)
                err_sys("Eroare signal( SIGALRM, ...)");
        alarm( 10);
        if ((n=read( 0, line, MAXLINE)) < 0)
                err_sys("Eroare read");
        alarm(0);
        write(1, line, n);
        exit(0);
}
static void sig_alarm(int sig)
{
        return;
}

```

# nivelul 0
Un proces care creaza alt proces iar noul proces creat trimite un semnal de tip alarm catre procesul parinte dupa 3 secunde

# nivelul 1
Un proces care creaza alt proces, 
iar noul proces creaza alt proces la randul lui, 
iar al treilea proces trimite un semnal de tip SIGUSR catre primul proces dupa 4 secunde iar primul proces trateaza cu succes acel semnal primit

# nivel 11
Un proces care creaza alt proces, 
iar noul proces creaza alt proces la randul lui, 
iar primul proces trimite un semnal de tip alarm catre procesul 3 dupa 3 secunde iar procesul 3 trateaza cu succes acel semnal primit

# nivel 2
Un proces care creaza alt proces, iar noul proces creaza alt proces la randul lui. 
Al treilea proces trimite un semnal de tip SIGUSR catre primul proces dupa 2 secunde 
iar primul proces trateaza cu succes acel semnal primit si trimite un semnal de tip SIGALARM catre procesul 2 dupa e a tratat semnalul
iar procesul 2 trateaza cu succes semnaul primit
