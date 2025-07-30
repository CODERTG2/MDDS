from bert_score import score as bert_score
import nltk
from nltk.tokenize import word_tokenize
from nltk.util import ngrams
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

nltk.download('punkt')

from main import normal_search, deep_search

test_set = [
    {
        "question": "What is the primary purpose of the Mobile Device Interface (MDI)?",
        "answer": "The MDI enables electrochemical diagnostic tests by integrating a potentiostat, microcontroller, and Bluetooth module with a mobile device. It allows for point-of-care and remote medical diagnostics by leveraging mobile device capabilities like display, computation, and connectivity"
    },
    {
        "question": "What types of medical diagnostics can electrochemical techniques support?",
        "answer": "Electrochemical techniques can support diagnostics for conditions such as cancer, cardiovascular diseases, and antibiotic susceptibility, using characteristic redox reactions of biochemical samples"
    },
    {
        "question": "How does the Cyclic Voltammetry (CV) method work in the MDI system?",
        "answer": "CV applies a triangular voltage waveform across three electrodes in a biochemical sample. The resulting current response is analyzed for characteristic redox peaks, which are used to identify chemical properties relevant for diagnostics"
    },
    {
        "question": "What hardware components make up the potentiostat interface in the MDI system?",
        "answer": "The interface includes a potentiostat module, a TI MSP430 microcontroller, a Panasonic CC2560 Bluetooth module, a power source (battery), and test electrode connectors"
    },
    {
        "question": "Why is vibration diagnostics critical for the International Linear Collider (ILC)?",
        "answer": "Achieving nanometer-scale beam sizes and precise alignment of accelerator components is essential for ILC’s high luminosity. Vibration diagnostics help maintain static and dynamic alignment, minimizing emittance degradation and beam jitter"
    },
    {
        "question": "What are some of the sensor technologies used for vibration diagnostics in the ILC cryomodules?",
        "answer": "Technologies include piezoelectric accelerometers, geophones, Wire Position Monitors (WPM), and interferometric displacement sensors. Each has strengths and limitations in terms of frequency sensitivity, cryogenic compatibility, and resolution"
    },
    {
        "question": "What limitations were observed with piezoelectric accelerometers in cryogenic environments at the ILC?",
        "answer": "Piezoelectric accelerometers lose sensitivity when cooled to cryogenic temperatures (e.g., 4.5 K), making them insufficiently sensitive for low-frequency (1–10 Hz) diagnostics in the linac. Their resolution is limited to the micro-g level"
    },
    {
        "question": "What diagnostic improvements were proposed for the Final Doublet (FD) region in the ILC?",
        "answer": "Proposed diagnostics for the FD region include electrochemical seismometers (MET-based), laser interferometry for displacement measurement, and non-contact position sensors like core-less LVDTs, which are effective in high-magnetic, cryogenic, and radiation-rich environments"
    },
    {
        "question": "What role does the Android application play in the MDI system?",
        "answer": "The Android app handles user input for scan settings, manages Bluetooth communications, plots electrochemical results, and stores data in CSV format. It serves as the user interface and processing hub for diagnostic tests"
    },
    {
        "question": "What were the results when validating the MDI system against a commercial potentiostat (CHI 1200B)?",
        "answer": "The MDI system showed peak potentials of 0.30 V and 0.13 V compared to 0.28 V and 0.18 V from the commercial device, with errors of 7.14% and 27.78%. The trends matched well, validating the MDI as a functional prototype despite minor inaccuracies"
    }
]

results = []
for item in test_set:
    question = item["question"]
    print(f"\n🔍 Testing question: {question}")
    try:
        answer = deep_search(question, 0.5)
        print(f"✅ Answer: {answer}\n")
        results.append({"question": question, "answer": answer})
    except Exception as e:
        print(f"❌ Error for question: {question}\n{e}")

# Metrics for RAG evaluation
def exact_match(pred, ref):
    return int(pred.strip().lower() == ref.strip().lower())

def f1_score(pred, ref):
    pred_tokens = word_tokenize(pred.lower())
    ref_tokens = word_tokenize(ref.lower())
    common = set(pred_tokens) & set(ref_tokens)
    if not common:
        return 0.0
    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(ref_tokens)
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)

def rouge_l(pred, ref):
    pred_tokens = word_tokenize(pred.lower())
    ref_tokens = word_tokenize(ref.lower())
    # Longest Common Subsequence
    m, n = len(pred_tokens), len(ref_tokens)
    dp = [[0]*(n+1) for _ in range(m+1)]
    for i in range(m):
        for j in range(n):
            if pred_tokens[i] == ref_tokens[j]:
                dp[i+1][j+1] = dp[i][j] + 1
            else:
                dp[i+1][j+1] = max(dp[i][j+1], dp[i+1][j])
    lcs = dp[m][n]
    if m == 0 or n == 0:
        return 0.0
    prec = lcs / m
    rec = lcs / n
    if prec + rec == 0:
        return 0.0
    return 2 * prec * rec / (prec + rec)

def semantic_similarity(pred, ref, model):
    emb_pred = model.encode([pred])[0].reshape(1, -1)
    emb_ref = model.encode([ref])[0].reshape(1, -1)
    return float(cosine_similarity(emb_pred, emb_ref)[0][0])

# Load sentence transformer for semantic similarity
semantic_model = SentenceTransformer('pritamdeka/S-BioBert-snli-multinli-stsb', device='cpu')

em_scores, f1_scores, rouge_scores, sem_scores = [], [], [], []
for item, result in zip(test_set, results):
    ref = item["answer"]
    pred = result["answer"]
    em = exact_match(pred, ref)
    f1 = f1_score(pred, ref)
    rouge = rouge_l(pred, ref)
    sem = semantic_similarity(pred, ref, semantic_model)
    em_scores.append(em)
    f1_scores.append(f1)
    rouge_scores.append(rouge)
    sem_scores.append(sem)
    print(f"Question: {item['question']}")
    print(f"Expected: {ref}")
    print(f"Actual:   {pred}")
    print(f"Exact Match: {em}, F1: {f1:.2f}, ROUGE-L: {rouge:.2f}, Semantic: {sem:.2f}\n")


bert_scores = []
for item, result in zip(test_set, results):
    ref = item["answer"]
    pred = result["answer"]
    em = exact_match(pred, ref)
    f1 = f1_score(pred, ref)
    rouge = rouge_l(pred, ref)
    sem = semantic_similarity(pred, ref, semantic_model)
    # BERTScore (using default model)
    P, R, F1 = bert_score([pred], [ref], lang="en", rescale_with_baseline=True)
    bert_f1 = F1[0].item()
    bert_scores.append(bert_f1)
    em_scores.append(em)
    f1_scores.append(f1)
    rouge_scores.append(rouge)
    sem_scores.append(sem)
    print(f"Question: {item['question']}")
    print(f"Expected: {ref}")
    print(f"Actual:   {pred}")
    print(f"Exact Match: {em}, F1: {f1:.2f}, ROUGE-L: {rouge:.2f}, Semantic: {sem:.2f}, BERTScore F1: {bert_f1:.2f}\n")


print(f"\n=== METRIC SUMMARY ===")
print(f"Exact Match: {sum(em_scores)}/{len(em_scores)}")
print(f"F1 Score (avg): {sum(f1_scores)/len(f1_scores):.2f}")
print(f"ROUGE-L (avg): {sum(rouge_scores)/len(rouge_scores):.2f}")
print(f"Semantic Similarity (avg): {sum(sem_scores)/len(sem_scores):.2f}")
print(f"BERTScore F1 (avg): {sum(bert_scores)/len(bert_scores):.2f}")