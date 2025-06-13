import os
import json
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
        api_key="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",
 # 🔒 غيّره هنا لو نشرته علنًا
)

BATCH_SIZE = 5

def process_txt_files(input_folder, output_json_path = None):
    batches = []
    current_batch = ""
    count = 0

    for filename in sorted(os.listdir(input_folder)):
        if filename.endswith(".text"):
            with open(os.path.join(input_folder, filename), "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    current_batch += f"\n\n--- Page {filename} ---\n{content}"
                    count += 1
                    if count == BATCH_SIZE:
                        batches.append(current_batch)
                        current_batch = ""
                        count = 0

    if current_batch.strip():
        batches.append(current_batch)

    results = []

    for idx, batch_text in enumerate(batches):
        print(f"\n📦 معالجة الدفعة {idx + 1} من {len(batches)}")

        prompt = f"""
You are an intelligent MCQ extractor.

Your goal is to extract structured multiple-choice questions from this text.

Only return a JSON array. Do NOT include explanations or formatting like ```json.

Each question should be an object with:
- "question"
- "options": list of strings starting with A., B., etc.
- "answer" (if found)
- "explanation" (if found)
- "page"
- "category" (if found)

Text:
{batch_text}
"""

        try:
            response = client.chat.completions.create(
                model="openai/gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=4000,
            )

            if not response.choices or not response.choices[0].message:
                print("❌ لا يوجد رد من LLM.")
                continue

            result_text = response.choices[0].message.content.strip()
            print("🧠 الرد الأولي من LLM:\n", result_text)

            # إزالة الغلاف إن وجد
            if result_text.startswith("```json"):
                result_text = result_text[len("```json"):].strip()
            if result_text.startswith("```"):
                result_text = result_text[len("```"):].strip()
            if result_text.endswith("```"):
                result_text = result_text[:-3].strip()

            parsed = json.loads(result_text)
            cleaned = [
                {k: v for k, v in item.items() if v is not None}
                for item in parsed if isinstance(item, dict)
            ]
            results.extend(cleaned)

        except Exception as e:
            print(f"❌ خطأ في الدفعة {idx + 1}: {e}")
            
            continue

        if not results:
         print("⚠️ لم يتم استخراج أي أسئلة.")
         return []

    # لو كان فيه مسار حفظ، نحفظه (اختياري)
    if output_json_path:
        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        with open(output_json_path, "w", encoding="utf-8") as out_f:
            json.dump(results, out_f, ensure_ascii=False, indent=2)
        print(f"✅ JSON IS DONE: {output_json_path}")

    return results 

