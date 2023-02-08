#include <stdio.h>
#include <err.h>
#include <fcntl.h>
#include <unistd.h>
#include <qcustomplot.h>

// g++ kevään_tallennus.c -Wall `pkg-config --cflags --libs Qt5Widgets gsl` -lqcustomplot -fpic -fpermissive

typedef short mk_ytyyppi;
typedef short mk_xtyyppi;
#include "mkts.c"

int _num;
#define R(f,a,b) if((_num=read(f, a, b)) != (int)(b)) warn("read rivillä %i (%i != %i)", __LINE__, _num, (int)(b))

struct Ikkuna: public QWidget {
    Ikkuna(QWidget* parent = NULL) {
	this->plot = new QCustomPlot;
	this->plot->plotLayout()->clear();
    }
    ~Ikkuna() {
	delete this->plot;
    }
    void pisteet(short*, short*, int, int);
    QCustomPlot* plot;
};

void Ikkuna::pisteet(short* y, short* x, int pit, int n) {
    QVector<double> xv(pit), yv(pit);
    for(int i=0; i<pit; i++) {
	xv[i] = x[i];
	yv[i] = y[i];
    }
    auto ax = new QCPAxisRect(this->plot);
    this->plot->plotLayout()->addElement(n%2, n/2, ax);
    QCPGraph* graph = this->plot->addGraph(ax->axis(QCPAxis::atBottom), ax->axis(QCPAxis::atLeft));
    graph->setData(xv, yv);
    graph->setLineStyle(QCPGraph::lsNone);
    graph->setScatterStyle(QCPScatterStyle(QCPScatterStyle::ssDisc, 7));
    graph->rescaleAxes();
}

int main() {
    int fd = open("kevään_päivät.bin", O_RDONLY);
    int vuosia, ik;
    R(fd, &vuosia, 1);
    R(fd, &ik, 1);
    short alut[ik][vuosia];
    short loput[ik][vuosia];
    short vuodet[vuosia];
    R(fd, alut, ik*vuosia*sizeof(short));
    R(fd, loput, ik*vuosia*sizeof(short));
    close(fd);

    for(int i=0; i<vuosia; i++)
	vuodet[i] = 2011+i;

    int nolla = 0;
    QApplication app(nolla, NULL);
    Ikkuna ikk;
    for(int i=0; i<ik; i++) {
	/*
	float y[vuosia];
	for(int j=0; j<vuosia; j++)
	    y[j] = alut[i][j];
	    */
	float p = mannkendall(alut[i], vuosia);
	float a = ts_kulmakerroin_yx(alut[i], vuodet, vuosia);
	//float b = ts_vakiotermi_yx(y, vuodet, vuosia, a);
	printf("%f, %f\n", p, a);
	ikk.pisteet(alut[i], vuodet, vuosia, i);
    }
    ikk.plot->show();
    return app.exec();
}
