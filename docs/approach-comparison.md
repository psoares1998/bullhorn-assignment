# Approach Comparison

## Possible Approaches

Several approaches were considered for classifying addresses to their country:

### 1. Layered Classification Pipeline (selected)

A rule-based system that parses the address into structural components (via libpostal) and extracts signals — country names, postal codes, city names, linguistic features — through a sequence of layers. Uses a voting system to combine signals when no single layer resolves the country with certainty.

### 2. ML Models

**TF-IDF + SVM/Logistic Regression** — Extract character n-grams from the address text and train a classifier. The model would learn that certain character patterns correlate with specific countries (e.g., `straß` with DE/AT, `rua` with PT). Simple to implement and fast at inference.

**Naive Bayes** — A probabilistic classifier that would estimate the likelihood of each country given the words or character sequences in the address. Works well for text classification problems and is very fast, though it assumes feature independence which may not hold for address components.

**CNN (Convolutional Neural Network)** — A character-level CNN could learn local patterns in address text by applying convolutional filters over character sequences. This is similar to n-grams but the patterns are learned automatically rather than hand-crafted. Would be effective at capturing postal code formats and language-specific character combinations.

**RNN / LSTM** — Recurrent models that process the address character by character or word by word, capturing sequential dependencies. Could learn that certain word orderings or structural patterns (e.g., street name before city in some countries, after in others) are indicative of a country.

**Transformer / BERT** — Fine-tuning a multilingual transformer model (e.g., mBERT, XLM-R) for address classification. These models are pre-trained on text in many languages and already understand multilingual patterns, which is relevant given that the dataset contains addresses in 10+ European languages.

### 3. LLM-based Classification

Using a large language model (external API or local model) that leverages world knowledge to identify the country. Would likely achieve the highest accuracy on edge cases, but adds latency and external dependencies.

## Why the Pipeline

The assignment provides two datasets with a clear purpose — cities with countries to **build** the service, and addresses with countries to **validate** it. It also requires the service to be self-contained, fast, and extendable to new countries with a documented process for updating the data.

The pipeline is the approach that best fits these constraints. It uses each dataset in its intended role (cities to build, addresses to validate), it requires no external calls at runtime, and extending to a new country is a data-only operation — add cities, country name variants, postal code patterns, and linguistic terms. No retraining or code changes needed.

The assignment also suggests a baseline (token-to-city lookup) and asks to identify its shortcomings and improve on them. The layered pipeline directly addresses each shortcoming with a specific, traceable solution, which aligns with the iterative improvement framing of the problem.
