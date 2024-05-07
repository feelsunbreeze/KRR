% Facts
game(gta_v).
game(the_legend_of_zelda_breath_of_the_wild).
game(the_last_of_us_part_ii).
game(fortnite).
game(minecraft).
game(overwatch).
game(celeste).
game(dark_souls_iii).

genre(gta_v, action_adventure).
genre(the_legend_of_zelda_breath_of_the_wild, action_adventure).
genre(the_last_of_us_part_ii, action_adventure).
genre(fortnite, battle_royale).
genre(minecraft, sandbox).
genre(overwatch, first_person_shooter).
genre(celeste, platformer).
genre(dark_souls_iii, action_role_playing).

platform(gta_v, ps4).
platform(gta_v, xbox_one).
platform(the_legend_of_zelda_breath_of_the_wild, switch).
platform(the_last_of_us_part_ii, ps4).
platform(fortnite, pc).
platform(fortnite, xbox_one).
platform(fortnite, ps4).
platform(minecraft, pc).
platform(minecraft, xbox_one).
platform(minecraft, ps4).
platform(overwatch, pc).
platform(overwatch, xbox_one).
platform(overwatch, ps4).
platform(celeste, pc).
platform(celeste, switch).
platform(dark_souls_iii, pc).
platform(dark_souls_iii, ps4).
platform(dark_souls_iii, xbox_one).

% Rulesy
multiplayer(Game) :- game(Game), genre(Game, Genre), member(Genre, [battle_royale, first_person_shooter]).
challenging(Game) :- game(Game), (genre(Game, action_role_playing); genre(Game, platformer)).
