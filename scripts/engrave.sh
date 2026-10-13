LB=/usr/local/lib/python3.13/dist-packages/lilypond-binaries/bin
f="$1"; b="${f%.musicxml}"; size="$2"
$LB/musicxml2ly "$f" -o "$b.ly" >/dev/null 2>&1
sed -i 's/\\set stanza = "1."//g' "$b.ly"; sed -i "1a #(set-global-staff-size $size)" "$b.ly"
$LB/lilypond -dno-point-and-click -o "$b" "$b.ly" >/dev/null 2>&1 && echo "ok $b.pdf"
