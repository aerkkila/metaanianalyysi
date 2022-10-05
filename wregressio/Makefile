all: wregressio.out wregressio1.out

wregressio.out: wregressio.c
	gcc ${@:.out=.c} -o $@ `pkg-config --libs nctietue2 gsl` -lm -g3 -gdwarf-2 -Wall -O3

wregressio1.out: wregressio.c
	gcc ${@:1.out=.c} -o $@ `pkg-config --libs nctietue2 gsl` -lm -g3 -gdwarf-2 -Wall -DIKIROUTA -O3
