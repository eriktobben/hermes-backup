# Train a BERT model for text classification.
# Uses transformers v5 API (processing_class, labels column).

# 1. Prepare labeled data
data = {"text": [...], "label": [...]}

# 2. Map labels to IDs
label_list = sorted(set(data["label"]))
label2id = {l: i for i, l in enumerate(label_list)}
id2label = {i: l for l, i in label2id.items()}

# 3. Create Dataset
import pandas as pd
from datasets import Dataset, DatasetDict
from sklearn.model_selection import train_test_split

df = pd.DataFrame(data)
df["labels"] = df["label"].map(label2id)
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df["label"])

dataset = DatasetDict({
    "train": Dataset.from_pandas(train_df[["text", "labels"]]),
    "test": Dataset.from_pandas(test_df[["text", "labels"]]),
})

# 4. Tokenize
from transformers import AutoTokenizer

MODEL_NAME = "NbAiLab/nb-bert-base"  # or distilbert-base-uncased, bert-base-multilingual-cased
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def tokenize(batch):
    return tokenizer(batch["text"], padding="max_length", truncation=True, max_length=128)

dataset = dataset.map(tokenize, batched=True)
dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

# 5. Load model
from transformers import AutoModelForSequenceClassification

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(label_list),
    id2label=id2label,
    label2id=label2id,
)

# 6. Train
from transformers import TrainingArguments, Trainer

args = TrainingArguments(
    output_dir="./model-output",
    eval_strategy="epoch",
    num_train_epochs=5,
    per_device_train_batch_size=8,
    learning_rate=2e-5,
    weight_decay=0.01,
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["test"],
    processing_class=tokenizer,  # transformers v5: was `tokenizer` in v4
)

trainer.train()

# 7. Save
model.save_pretrained("./min-modell")
tokenizer.save_pretrained("./min-modell")
print(f"Done. Labels: {label_list}")
