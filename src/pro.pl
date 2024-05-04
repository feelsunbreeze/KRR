word(Berries)
male(Ali)
male(Azaril)
male(Qasim)
female(Sarah)
female(Alisha)
food(Macaroni)
parent(Qasim, Ali)
parent(Ali, Azaril)
parent(Ali, Alisha)
parent(Sarah, Azaril)
parent(Sarah, Alisha)
likes(Ali, Macaroni)
has(Ali, car).
Spouse(Sarah, Ali).
wife(Sarah, Ali).

father(X, Y) :- parent(X, Y), male(X)
child(X, Y) :- parent(Y, X)
mother(X, Y) :- parent(X, Y), female(X)
son(X, Y) :- parent(Y, X), male(X)
daughter(X, Y) :- parent(Y, X), female(X)
brother(X, Y) :- male(x), parent(z, x), parent(z, y), neq(X, Y)
sister(X, Y):- female(x), parent(z, x), parent(z, y), neq(X, Y)
grandfather(X, Y, Z) :- parent(X, Z), parent(Z, Y), male(X)