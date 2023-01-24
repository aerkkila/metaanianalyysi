#!/bin/perl
$kansio = 'kuvat';
@kaudet = ('summer','freezing','winter','whole_year');
@lajisto = (['bog,fen,marsh', 'permafrost_bog,tundra_wetland,wetland'],
            ['nonpermafrost,sporadic', 'discontinuous,continuous']);

sub tee_muuttuja {
    $muuttuja = @_[0];
    for $kausi(@kaudet) {
        for $laji(@lajisto) {
	    print join('i',@laji);
	    @laji = @$laji;
	    $kmnt = 'gm convert';
	    for $laji(@lajit) {
		$kmnt = $kmnt . " +append $kansio/$muuttuja/$kausi,_{$laji}.png";
	    }
	    $kmnt = $kmnt . " -append kuvat/${1}_${kausi}_1.png";
	    print "$kmnt\n";
	}
    }
}

tee_muuttuja('emission');
tee_muuttuja('length');
