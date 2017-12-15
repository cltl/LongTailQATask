

Kappa score -> 0.59

## ROUND 1: Automatic checks + changes on annotations

1) eventtype 's' -> participants is always 'UNK'
2) checks EVENTTYPE (PARTICIPANTS):
    B (ALL)
    G (UNK)
    O (UNK)
    S (UNK)

Kappa score -> 0.70

## Round 2: remove mentions + map them automatically to annotations

Applying strategies **delete** and **EMT**

**delete**
I delete all annotations with the proposed mentions

**EMT** I apply the proposed strategy except if the event type is 'o'.

Kappa score -> 0.70