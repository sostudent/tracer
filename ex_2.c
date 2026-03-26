#include <stdio.h>
#include <unistd.h>

int main(void){
        printf("sleeping\n");
        int pid1 = fork();
        if (pid1 == 0){ 
                sleep(5);
                int pid2 = fork();
                if (pid2 == 0) { printf("sleep 1\n"); sleep(1);}
                printf("pid2 %d\n", pid2);
        }       
        printf("pid1 %d\n", pid1);
}
