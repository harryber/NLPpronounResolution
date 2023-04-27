# CS159 - NLP Final Project
Harry Berman, Ben Luo, and Aidan Wu

## Pronoun Resolution 
- Pronoun resolution refers to the determination of the reference that any given pronoun has.
- It is hard for computers to inherently determine the association of the pronoun, because of a lack of common sense.
- Hobb's Algorithm is one of the computer algorithms developed to help computers classify and resolve pronoun associations.

## Hobb's Algorithm
- The algorithm is based on analysis of the syntactic parse tree of a given sentence.
- The algorithm has a set of assumptions that it makes about sentence structures:
    1. Search for the referent (what the pronoun refers to) is always restricted to the left of the target
    2. Animate objects are generally referred to by male or female pronouns.
    3. Inanimate objects are usually referred to by neutral gender like terms, like "it".
    4. Pronouns generally only refer to something within a certain context, i.e. the previous three sentences, the previous paragraph, etc.

*Notes*: 2 and 3 make up the property that is known as the **gender agreement**.

## How we should go about it
-- Find the syntactice parse tree of the sentences.
-- Identify all 'S' or noun-classified (N) phrases.
-- contd

### References
[Hobbs Algorithm](https://medium.com/analytics-vidhya/hobbs-algorithm-pronoun-resolution-7620aa1af538)