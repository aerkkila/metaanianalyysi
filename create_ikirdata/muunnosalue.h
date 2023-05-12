static const int vnta_maxpit = 16000;
static struct alue_t {
    float lat0, lon0;
    int latpit, lonpit;
    float väli;
} alue = {
    .lat0 = 29,
    .lon0 = -180,
    .latpit = 55,
    .lonpit = 360,
    .väli = 1,
};
