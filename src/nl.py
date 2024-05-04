import pytholog as pl

kb = pl.KnowledgeBase("kb")

kb([
    "likes(noor, sausage)"
])

results = kb.query(pl.Expr("brother(X, Y)"))