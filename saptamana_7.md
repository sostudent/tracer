## probleme in fuctie de nivelul de cunostinte

# nivel -2
2.2. Compilati si rulati programul de mai jos si explicati rezultatul.

Pentru parametri folositi un fisier `numere.txt` care are pe doua linii numerele de la 0 la 9 si un nou nume de fisier creat anterior cu `touch nume_fisier`.

Adica `./main numere.txt nume_fisier`
```c
#include <fcntl.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
int fdR, fdW;
char c;
int rd_wr();
int main(int argc, char * argv[])
{
        if ( argc != 3) exit(1);
        if (( fdR=open( argv[1], O_RDONLY)) == 1)
                printf( "Eroare open1\n");
        if (( fdW=open( argv[2], O_WRONLY)) == 1)
                printf( "Eroare open2\n");
        fork(); rd_wr(); exit(0);
}
int rd_wr() {
        while (1 == 1){
                if (read( fdR, &c, 1) == 0) return 0;
                write(fdW, &c, 1);
        }
}
```


# nivel -1
2.2. Compilati si rulati programul de mai jos si explicati rezultatul. Apoi modificati programul astfel incat sa functioneze corect (dupa ce identificati multiplele probleme, cel putin doua).
```c
#include <fcntl.h>
#include <unistd.h>
#include "hdr.h"
int fdR, fdW;
char c;
main( int argc, char * argv[])
{
        if ( argc != 3) exit(1);
        if (( fdR=open( argv[1], O_RDONLY)) == 1)
                err_sys( "Eroare open1\n");
        if (( fdW=open( argv[2], O_WRONLY)) == 1)
                err_sys( "Eroare open2\n");
        fork(); rd_wr(); exit(0);
}
rd_wr() {
        for ever {
                if ( read( fdR, &c, 1) == 0) return;
                write( fdW, &c, 1);
        }
}
```


# nivelul 0
Un proces care creaza alt proces iar noul proces creat afiseaza pidul procesului parinte

# nivelul 1
Un proces care creaza alt proces, iar noul proces creaza alt proces la randul lui, iar al treilea proces afiseaza pidurile proceselor anterioare in ordine, adica pid proces 1 si apoi pid proces 2

# nivel 11
Un proces care creaza alt proces, iar noul proces creaza alt proces la randul lui, iar primul proces afiseaza pidurile celorlalte 2 procese in ordine, adica pid proces 2 si apoi pid proces 3

# nivel 2
Un proces care creaza doua procese, apoi cele doua procese la randul lor creaza alt proces, si ultimele doua procese afiseaza pidurile proceselor parinte in ordinea in care au fost create

# nivel 3
Un proces care creaza doua procese, apoi cele doua procese la randul lor creaza alte 3 procese, fiecare proces din cele 6 procese de la final afiseaza pidurile proceselor parinte in ordinea in care au fost create

# nivel 4
Un proces care creaza doua procese, apoi cele 2 procese creaza la randul lor alte 3 procese, iar fiecare din cele 6 procese de la final afiseaza pidurile proceselor care nu au fost parinte direct dar au fost unul din cele doua proese create la nivelul 2

# nivel 5
Un proces care creaza trei procese, apoi cele 3 procese creaza la randul lor alte 3 procese, iar fiecare din cele 9 procese de la final afiseaza pe 4 linii
 - pidul primului proces
 - pidul procesului parinte
 - pidurile celorlalte 8 procese de pe ultimul nivel (nu conteaza ordinea)
 - pidurile celorlalte 2 procese de pe nivelul 2 care nu sunt parintele direct (nu conteaza ordinea)

# nivel 6
Un proces care creaza 3 procese, apoi cele 3 procese creaza la randul lor alte 3 procese, iar procesul initial afieaza cele 9 piduri pentru toate cele 9 procese de pe ultimul nivel (nu conteaza ordinea in care se afiseaza pidurile).
