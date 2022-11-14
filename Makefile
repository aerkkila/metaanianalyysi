all: vuotaul_00.target vuotaul_10.target vuotaul_01.target vuotaul_02.target kuvat taulukot.out

vuotaul_00.target: vuotaul_köppen_pri.csv vuotaul_köppen_post.csv vuotaul_ikir_pri.csv vuotaul_ikir_post.csv vuotaul_wetland_pri.csv vuotaul_wetland_post.csv
	cat vuotaulukot/*_pri_*.csv > vuotaul_pri.csv
	cat vuotaulukot/*_post_*.csv > vuotaul_post.csv
vuotaul_00.out:
	gcc -Wall -g -O2 vuotaul_yleinen.c -o $@ `pkg-config --libs nctietue2` -lm -DKOSTEIKKO=0 -Dkosteikko_kahtia=0
vuotaul_wetland_post.csv: vuotaul_00.out
	./vuotaul_00.out wetl post
vuotaul_wetland_pri.csv: vuotaul_00.out
	./vuotaul_00.out wetl pri
vuotaul_köppen_post.csv: vuotaul_00.out
	./vuotaul_00.out köpp post
vuotaul_köppen_pri.csv: vuotaul_00.out
	./vuotaul_00.out köpp pri
vuotaul_ikir_post.csv: vuotaul_00.out
	./vuotaul_00.out ikir post
vuotaul_ikir_pri.csv: vuotaul_00.out
	./vuotaul_00.out ikir pri

# calculates climate and permafrost class data with only their wetland areas into vuotaulukot/*k1.csv
vuotaul_10.target: vuotaul_köppen_post10.csv vuotaul_ikir_post10.csv
vuotaul_10.out:
	gcc -Wall -g -O2 vuotaul_yleinen.c -o $@ `pkg-config --libs nctietue2` -lm -DKOSTEIKKO=1 -Dkosteikko_kahtia=0
vuotaul_köppen_post10.csv: vuotaul_10.out
	./vuotaul_10.out köpp post
vuotaul_ikir_post10.csv: vuotaul_10.out
	./vuotaul_10.out ikir post

# calculates wetland data without the mixed area into vuotaulukot/kahtia/*
vuotaul_01.target: vuotaul_wetland_post01.csv
vuotaul_01.out:
	gcc -Wall -g -O2 vuotaul_yleinen.c -o $@ `pkg-config --libs nctietue2` -lm -DKOSTEIKKO=0 -Dkosteikko_kahtia=1
vuotaul_wetland_post01.csv: vuotaul_01.out
	./vuotaul_01.out wetl post

# calculates wetland data with only the mixed area into vuotaulukot/kahtia_keskiosa/*
vuotaul_02.target: vuotaul_wetland_post02.csv
vuotaul_02.out:
	gcc -Wall -g -O2 vuotaul_yleinen.c -o $@ `pkg-config --libs nctietue2` -lm -DKOSTEIKKO=0 -Dkosteikko_kahtia=2
vuotaul_wetland_post02.csv: vuotaul_02.out
	./vuotaul_02.out wetl post

kuvat:
	./köppikir_kartta.py -s
	./kaudet_laatikko.py -s
	./bawld_ikir_kartta.py -s
	./xvuo_laatikko.py -s
	./vuojakaumalaatikko.py -s
	./vuojakaumalaatikko_vuosittain.py -s

vuotaul.out:
	gcc vuotaul_latex.c -O2 -o $@
	./$@
	gcc vuotaul_latex.c -DKOST_KAHTIA=1 -O2 -o $@
	./$@
	gcc vuotaul_latex.c -DKOST_KAHTIA=2 -O2 -o $@
	./$@
	gcc vuotaul_latex.c -DKOSTEIKKO=1 -O3 -o $@
	./$@

taulukot.out: vuotaul.out
	./köppikir_taulukko.py
	gcc lattaul.c -O1 -o $@
	./$@
