#include <geodesic.h>
#include <stdio.h>
#include <nctietue3.h>

int main() {
    double *lat, *lon, latväli05, lonväli;
    int latpit;

    /* Alustetaan yllä olevat. */
    nct_readm_ncf(set, "aluemaski.nc", nct_rlazy);
    nct_var* v = nct_loadg_as(&set, "lat", NC_DOUBLE);
    latpit = v->len;
    lat = v->data;
    latväli05 = (lat[1]-lat[0]) * 0.5;
    v = nct_loadg_as(&set, "lon", NC_DOUBLE);
    lon = v->data;
    lonväli = lon[1]-lon[0];

    /* Alustetaan geoidi. */
    struct geod_geodesic g;
    geod_init(&g, 6378137, 1/298.257222101); // WGS84
    double ala1, ala2;

    FILE* H = fopen("pintaalat.h", "w");
    FILE* py = fopen("pintaalat.py", "w");
    fprintf(H, "static const double pintaalat[] = {\n    ");
    fprintf(py, "pintaalat = [\n    ");

    for(int j=0; ; j++) {
	geod_geninverse(&g,
		lat[j]-latväli05, 0, lat[j]-latväli05, lonväli,
		NULL, NULL, NULL, NULL, NULL, NULL, &ala1);
	geod_geninverse(&g,
		lat[j]+latväli05, 0, lat[j]+latväli05, lonväli,
		NULL, NULL, NULL, NULL, NULL, NULL, &ala2);
	double ala = (ala2-ala1) * 1e-6;
	fprintf(H, "%lf", ala);
	fprintf(py, "%lf", ala);
	if (j==latpit-1)
	    break;
	if (!((j+1)%7)) {
	    fprintf(H, ",\n    ");
	    fprintf(py, ",\n    ");
	}
	else {
	    fprintf(H, ", ");
	    fprintf(py, ", ");
	}
    }
    fprintf(H, "\n};\n");
    fprintf(py, "\n]\n");
    fclose(H);
    fclose(py);
    nct_free1(&set);
}
