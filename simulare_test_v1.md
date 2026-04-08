# nivel 0
Un proces care creaza alt proces iar noul proces creat afiseaza pidul procesului parinte.

# nivel 1
Un proces care creaza alt proces, iar noul proces creaza alt proces la randul lui.

Al treilea proces afiseaza pidurile proceselor anterioare in ordine, adica pid proces 1 si apoi pid proces 2.

# nivel 2
Un proces care creaza alt proces iar noul proces creat trimite un semnal de tip alarm catre procesul parinte dupa 3 secunde.

Procesul parinte afiseaza pidul procesului fiu dupa primirea semnalului de tip alarm.

# nivel 3
Un proces care creaza alt proces, iar noul proces creaza alt proces la randul lui.

Al treilea proces trimite un semnal de tip SIGUSR catre primul proces dupa 4 secunde iar primul proces trateaza cu succes acel semnal primit
si afiseaza pidul procesului care a trimis semnalul (adica pidul procesului 3).

# nivel 4
Un proces care creaza un nou proces lar noul proces creat trimite printr-un pipe pidul primului process catre primul proces.

Primul proces afiseaza ceea ce a primit prin pipe.

# nivel 5
Un proces care creaza alt proces, iar noul proces creaza alt proces la randul lui.

Al treilea proces trimite printr-un pipe pidul procesului 1 catre primul proces. Primul proces afiseaza ce a primit prin pipe.

