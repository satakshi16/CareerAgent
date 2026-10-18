---
name: explain-simply
description: Explain technical concepts and project stories in plain language with everyday analogies and small concrete examples that a non-technical person would follow. Load at I0_intake for technical and hiring_manager rounds, and whenever teaching a concept.
---

# Explain It Simply

Every technical concept in the prep gets four parts:

1. **Plain definition:** one sentence with no jargon. If a term can't be avoided, define it in the same sentence.
2. **Everyday analogy:** from daily life (kitchen, library, post office, GPS, school exam), never from another technical field. Check that the mapping holds in both directions.
3. **Tiny example with numbers:** a concrete case small enough to do in your head.
4. **Where the analogy breaks:** one line. Interviewers probe here, and saying it shows real understanding.

Add a **"Say it to a stakeholder"** line where it fits: 1 to 2 sentences about what the concept means for cost, time, risk, or customers.

## Two worked examples

**Retrieval-augmented generation (RAG)**
- Plain: the model looks up relevant documents first, then answers using them.
- Analogy: an open-book exam. The student (the model) still writes the answer, but checks the textbook (your documents) first instead of relying on memory.
- Example: a policy bot gets "How many vacation days carry over?", pulls the 3 most similar paragraphs out of 2,000 HR pages, and answers "5 days", citing section 4.2.
- Breaks: a student knows which chapter to open. Retrieval can pull the wrong pages, so the answer is only as good as the search.
- Say it to a stakeholder: "It answers from our own documents and shows its source, so people can check it, and we update it by updating the documents rather than retraining."

**Precision vs recall**
- Plain: precision is how many of the flagged items were truly bad. Recall is how many of the truly bad items got flagged.
- Analogy: fishing for tuna with a net. A small, careful net catches mostly tuna (high precision) but misses many. A huge net catches nearly all the tuna (high recall) plus a lot of other fish.
- Example: 100 fraud cases. The model flags 50 and 40 are fraud: precision 80%, recall 40%.
- Breaks: a fisher can see the catch right away. In real data, the true labels often arrive weeks later.
- Say it to a stakeholder: "We're choosing between wasting reviewer time on false alarms and letting fraud through. The right balance depends on what each mistake costs us."

## Quick analogy bank (check the fit before using)

Embeddings: GPS coordinates for meaning, so similar ideas sit close together. Overfitting: memorizing last year's exam answers instead of learning the subject. Vector database: a library shelved by topic, not alphabetically. Agent tool use: an assistant with a phone list who decides whom to call. Model evaluation: taste-testing before the dish goes out. Data drift: a store's sales model trained before a new mall opened nearby. Fine-tuning: a new hire's on-the-job training after a general degree. Latency vs throughput: one fast courier vs a truck that carries many parcels.

## HM project story (non-technical version)

Three sentences: the business problem in money, time, or people terms. What was built, in one plain sentence. The result, from sources only, and who used it.

## Rules

- One analogy per concept. Don't stack metaphors.
- Talk to an adult. Plain, not childish.
- Claims about the candidate still follow `no-fabrication`. Analogies and examples are teaching aids, so label invented numbers in examples as illustrations.
