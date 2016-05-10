Lokaverk VEF3A3U  - Daníel Theodórs Ólafsson

Nokkrir punktar:
flash('string') er texti sem myndast fyrir neðan navbar í template.html (get flashed messages)

app.before.request keyrist áður en hvert routing function er keyrt (connect db)
app.teardown.request keyrist eftir hvert routing function (close db)

jinja template: {% logic (if, for ..) %} {{ strings, values .. }}

gert er ráð fyrir að það sé til admin i gagnagrunni (þaes ef enginn er til í users table þá er ekki hægt að fara úr því að vera guest->staff og customer->klippimeistara nema í gegnum gagnagrunn.

mailserver var ekki að virka í skólanum en virkar fínt heima hjá mér (sjá: /appointments/book route)



