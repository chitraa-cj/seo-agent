import json
from config import client

def evaluate_result_for_openai(data):
    if 'error' in data:
        return 0, {"error": data['error']}
    
    scores = {
        'title': _score_title(data.get('title', '')),
        'meta_description': _score_meta_description(data.get('meta_description', '')),
        'headings': _score_headings(data.get('headings', [])),
        'content': _score_content(data.get('content', ''), data.get('word_count', 0)),
        'additional_elements': _score_additional_elements(data),
        'performance': _score_performance(data.get('execution_time', 10))
    }
    
    total_score = sum(scores.values())
    openai_quality = _create_quality_report(scores, total_score)
    return total_score, openai_quality

def generate_seo_analysis(data, website_url, niche, tagline):
    if not client:
        return {"error": "OpenAI API key not found"}
    
    if 'error' in data:
        return {"error": f"Cannot generate SEO analysis: {data['error']}"}
    
    try:
        prompt = f"""You are an expert SEO consultant analyzing a website for on-page optimization. 
        Website URL: {website_url}
        Niche: {niche}
        Tagline: {tagline}
        Website data: {json.dumps({k: v for k, v in data.items() if k != 'content'}, indent=2)}
        Content excerpt: {data.get('content', '')[:1500]}"""
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert SEO consultant providing actionable advice for website optimization."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000
        )
        
        return {"analysis": response.choices[0].message.content, "success": True}
    except Exception as e:
        return {"error": f"Error generating SEO analysis: {str(e)}"}

# Helper functions for scoring
def _score_title(title):
    if not title or title == "No title found":
        return 0
    title_length = len(title)
    if 10 <= title_length <= 60: return 20
    if 5 <= title_length < 10 or 60 < title_length <= 80: return 15
    return 10

def _score_meta_description(meta):
    if not meta or meta == "No meta description found":
        return 0
    meta_length = len(meta)
    if 50 <= meta_length <= 160: return 15
    if 30 <= meta_length < 50 or 160 < meta_length <= 200: return 10
    return 5

def _score_headings(headings):
    if len(headings) >= 3: return 15
    if len(headings) >= 1: return 10
    return 5

def _score_content(content, word_count):
    actual_word_count = word_count or len(content.split())
    if actual_word_count >= 500: return 30
    if actual_word_count >= 300: return 25
    if actual_word_count >= 100: return 15
    return 10

def _score_additional_elements(data):
    score = 0
    if data.get('link_count', 0) > 0: score += 10
    if data.get('image_count', 0) > 0: score += 5
    if data.get('images_with_alt', 0) > 0: score += 5
    return score

def _score_performance(execution_time):
    if execution_time <= 2: return 10
    if execution_time <= 5: return 8
    if execution_time <= 10: return 6
    return 4

def _create_quality_report(scores, total_score):
    quality = {
        "completeness": min(100, total_score / 1.1),
        "detail_scores": scores,
        "strengths": [],
        "weaknesses": []
    }
    
    if scores['title'] >= 15: quality["strengths"].append("Strong title extraction")
    elif scores['title'] <= 10: quality["weaknesses"].append("Poor title extraction")
    
    if scores['meta_description'] >= 10: quality["strengths"].append("Good meta description")
    elif scores['meta_description'] <= 5: quality["weaknesses"].append("Weak meta description")
    
    if scores['content'] >= 25: quality["strengths"].append("Rich content extraction")
    elif scores['content'] <= 15: quality["weaknesses"].append("Limited content extraction")
    
    quality["strengths"].append("Good heading structure") if scores['headings'] >= 10 else quality["weaknesses"].append("Poor heading extraction")
    
    if scores['additional_elements'] >= 15: quality["strengths"].append("Comprehensive additional elements")
    elif scores['additional_elements'] <= 5: quality["weaknesses"].append("Missing important SEO elements")
    
    quality["strengths"].append("Excellent performance") if scores['performance'] >= 8 else quality["weaknesses"].append("Slow extraction time")
    
    return quality