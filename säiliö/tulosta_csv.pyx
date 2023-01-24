cdef char* csvvari(float arvo):
    return (
            b'' if 0
            else b'\033[1;91m' if arvo < 0.01
            else b'\033[94m' if arvo < 0.02
            else b'\033[92m' if arvo < 0.05
            else b''
            )

cdef char _palaute[32]
cdef char* latexluku(float arvo, float luku):
    if arvo < 0.01:
        sprintf(_palaute, "\\textbf{%.3f}", luku)
    elif arvo < 0.02:
        sprintf(_palaute, "\\textbf{(%.3f)}", luku)
    elif arvo < 0.05:
        sprintf(_palaute, "%.3f", luku)
    else:
        sprintf(_palaute, "(%.3f)", luku)
    return _palaute

cdef tulosta_lista(listalista):
    cdef FILE* csv = fopen("trendit.csv", "w")
    cdef FILE* tex = fopen("trendit.tex", "w")
    cdef int i, j, k, ntexmuutt=len(latexmuutt), nmuutt=len(muuttujat)
    cdef float luku, arvo
    assert(kausia==4)

    # latex-tiedoston alustaminen
    fprintf(tex, "\\begin{tabular}{l")
    for i in range(ntexmuutt):
        fprintf(tex, b"|")
        fprintf(tex, b"r"*kausia)
    fprintf(tex, "}\n")
    for i in range(ntexmuutt):
        fprintf(tex, " & \\multicolumn{%i}{c}{%s}", kausia, bytes(variables[latexmuutt[i]].encode('utf-8')))
    fprintf(tex, " \\\\\n");
    for i in range(ntexmuutt):
        for j in range(kausia):
            fprintf(tex, " & {%s}", bytes(kaudet_ulos[j]))
    fprintf(tex, " \\\\\n\\midrule\n")

    # csv:n alustaminen
    for i in range(nmuutt):
        fprintf(csv, ",%s", bytes(muuttujat[i]))
        fprintf(csv, b","*(kausia-1))
    fprintf(csv, '\n')
    for i in range(nmuutt):
        for j in range(kausia):
            fprintf(csv, ",%s", bytes(kaudet_ulos[j]))
    fprintf(csv, '\n')

    cdef int kausijarj[4]
    for i in range(kausia):
        for j in range(kausia):
            if kaudet[i] == listalista[0][j]['nimi'].split(b',')[0]:
                kausijarj[i] = j
                break
        else:
            printf("varoitus: %s\n", bytes(kaudet[i]))

    for k in range(0,len(listalista[0]),4):
        nimi = bytes(listalista[0][k]['nimi'].split(b',')[1])
        fprintf(csv, "%s", bytes(nimi))
        fprintf(tex, "%s", bytes(nimi))
        for j in range(nmuutt):
            latex = j in latexmuutt
            for i in range(kausia):
                luku = listalista[j][k+kausijarj[i]]['kulmak']*100
                arvo = listalista[j][k+kausijarj[i]]['parvot']
                fprintf(csv, ",%s%.3f\033[0m", csvvari(arvo), luku)
                if latex:
                    fprintf(tex, " & %s", latexluku(arvo, luku))
        fprintf(csv, "\n")
        fprintf(tex, " \\\\\n")

    fprintf(tex, "\\end{tabular}")
    fclose(tex)
    fclose(csv)

