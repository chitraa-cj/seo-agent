import json

def evaluate_result_for_openai(data):
    """Evaluate how well the data is suited for OpenAI SEO analysis"""
    if 'error' in data:
        return 0, {"error": data['error']}
    
    scores = {}
    
    # Title quality (0-20 points)
    title = data.get('title', '')
    if title and title != "No title found":
        title_length = len(title)
        if 10 <= title_length <= 60:
            scores['title'] = 20
        elif 5 <= title_length < 10 or 60 < title_length <= 80:
            scores['title'] = 15
        else:
            scores['title'] = 10
    else:
        scores['title'] = 0
    
    # Meta description quality (0-15 points)
    meta = data.get('meta_description', '')
    if meta and meta != "No meta description found":
        meta_length = len(meta)
        if 50 <= meta_length <= 160:
            scores['meta_description'] = 15
        elif 30 <= meta_length < 50 or 160 < meta_length <= 200:
            scores['meta_description'] = 10
        else:
            scores['meta_description'] = 5
    else:
        scores['meta_description'] = 0
    
    # Headings quality (0-15 points)
    headings = data.get('headings', [])
    if headings:
        if len(headings) >= 3:
            scores['headings'] = 15
        elif len(headings) >= 1:
            scores['headings'] = 10
        else:
            scores['headings'] = 5
    else:
        scores['headings'] = 0
    
    # Content quality (0-30 points)
    content = data.get('content', '')
    word_count = data.get('word_count', 0)
    if word_count or content:
        actual_word_count = word_count or len(content.split())
        if actual_word_count >= 500:
            scores['content'] = 30
        elif actual_word_count >= 300:
            scores['content'] = 25
        elif actual_word_count >= 100:
            scores['content'] = 15
        else:
            scores['content'] = 10
    else:
        scores['content'] = 0
    
    # Additional SEO elements (0-20 points)
    additional_score = 0
    if data.get('link_count', 0) > 0:
        additional_score += 10
    if data.get('image_count', 0) > 0:
        additional_score += 5
    if data.get('images_with_alt', 0) > 0:
        additional_score += 5
    scores['additional_elements'] = additional_score
    
    # Performance score based on execution time (0-10 points)
    execution_time = data.get('execution_time', 10)
    if execution_time <= 2:
        scores['performance'] = 10
    elif execution_time <= 5:
        scores['performance'] = 8
    elif execution_time <= 10:
        scores['performance'] = 6
    else:
        scores['performance'] = 4
    
    total_score = sum(scores.values())
    
    # Calculate quality for OpenAI prompt
    openai_quality = {
        "completeness": min(100, total_score / 1.1),  # Scale to 100%
        "detail_scores": scores,
        "strengths": [],
        "weaknesses": []
    }
    
    # Determine strengths and weaknesses
    if scores['title'] >= 15:
        openai_quality["strengths"].append("Strong title extraction")
    elif scores['title'] <= 10:
        openai_quality["weaknesses"].append("Poor title extraction")
        
    if scores['meta_description'] >= 10:
        openai_quality["strengths"].append("Good meta description")
    elif scores['meta_description'] <= 5:
        openai_quality["weaknesses"].append("Weak meta description")
        
    if scores['content'] >= 25:
        openai_quality["strengths"].append("Rich content extraction")
    elif scores['content'] <= 15:
        openai_quality["weaknesses"].append("Limited content extraction")
        
    if scores['headings'] >= 10:
        openai_quality["strengths"].append("Good heading structure")
    else:
        openai_quality["weaknesses"].append("Poor heading extraction")
        
    if scores['additional_elements'] >= 15:
        openai_quality["strengths"].append("Comprehensive additional elements")
    elif scores['additional_elements'] <= 5:
        openai_quality["weaknesses"].append("Missing important SEO elements")
        
    if scores['performance'] >= 8:
        openai_quality["strengths"].append("Excellent performance")
    elif scores['performance'] <= 5:
        openai_quality["weaknesses"].append("Slow extraction time")
    
    return total_score, openai_quality

def run_test_analysis(bs_data, fc_data, client):
    """Generate test prompts and analyze how OpenAI would respond"""
    if not client:
        return {
            "message": "OpenAI client not available. Please set your API key to run test analysis."
        }
    
    if 'error' in bs_data and 'error' in fc_data:
        return {
            "message": "Both crawlers failed. No test analysis possible."
        }
    
    # Create sample prompts from both crawlers
    bs_prompt = f"""Analyze SEO for a website.
    Title: {bs_data.get('title', 'Not available')}
    Meta Description: {bs_data.get('meta_description', 'Not available')}
    Headings: {bs_data.get('headings', [])}
    Content preview: {bs_data.get('content', 'Not available')[:500]}"""
    
    fc_prompt = f"""Analyze SEO for a website.
    Title: {fc_data.get('title', 'Not available')}
    Meta Description: {fc_data.get('meta_description', 'Not available')}
    Headings: {fc_data.get('headings', [])}
    Content preview: {fc_data.get('content', 'Not available')[:500]}"""
    
    # Evaluate prompt quality with OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in SEO and data quality analysis. Your task is to compare two different sets of website data and determine which would be more effective for SEO analysis. Provide a detailed technical comparison."},
                {"role": "user", "content": f"""Compare these two data extractions from the same website and determine which would be more effective for SEO analysis.
                
                BeautifulSoup Extraction:
                {json.dumps({k: v for k, v in bs_data.items() if k != 'content'}, indent=2)}
                Content length: {len(bs_data.get('content', ''))} characters
                
                Firecrawl Extraction:
                {json.dumps({k: v for k, v in fc_data.items() if k != 'content'}, indent=2)}
                Content length: {len(fc_data.get('content', ''))} characters
                
                Compare them on:
                1. Data completeness and accuracy for SEO analysis
                2. Content extraction quality
                3. Structured data capture
                4. Technical advantages/disadvantages
                5. Which would produce better SEO analysis results and why
                
                Provide your conclusion about which tool a developer should choose for SEO analysis purposes.
                """}
            ],
            max_tokens=1000
        )
        return {
            "message": "Analysis completed successfully",
            "comparison": response.choices[0].message.content,
            "bs_prompt_length": len(bs_prompt),
            "fc_prompt_length": len(fc_prompt)
        }
    except Exception as e:
        return {
            "message": f"Error analyzing data: {str(e)}"
        }

def generate_seo_analysis(data, website_url, niche, tagline, client):
    """Generate SEO analysis with OpenAI"""
    if not client:
        return {
            "error": "OpenAI API key not found. Please set your API key to generate SEO analysis."
        }
    
    if 'error' in data:
        return {
            "error": f"Cannot generate SEO analysis: {data['error']}"
        }
    
    try:
        # Create a prompt for OpenAI
        prompt = f"""You are an expert SEO consultant analyzing a website for on-page optimization. 
        
        Website URL: {website_url}
        Niche: {niche}
        Tagline: {tagline}
        
        Website data:
        Title: {data.get('title', 'Not available')}
        Meta Description: {data.get('meta_description', 'Not available')}
        Headings: {json.dumps(data.get('headings', []))}
        Word Count: {data.get('word_count', 0)}
        Links: {data.get('link_count', 0)}
        Images: {data.get('image_count', 0)} (with alt text: {data.get('images_with_alt', 0)})
        
        Content excerpt:
        {data.get('content', 'Not available')[:1500]}
        
        Provide a comprehensive SEO analysis including:
        1. Title tag evaluation and suggestions for improvement
        2. Meta description assessment and recommendations
        3. Heading structure analysis
        4. Content quality assessment (uniqueness, relevance, readability)
        5. Internal linking recommendations
        6. Image optimization suggestions
        7. Overall SEO score (out of 100)
        8. Top 3 prioritized action items to improve SEO
        
        Format the response as detailed markdown sections with clear headings.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert SEO consultant providing actionable advice for website optimization."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000
        )
        
        return {
            "analysis": response.choices[0].message.content,
            "success": True
        }
    except Exception as e:
        return {
            "error": f"Error generating SEO analysis: {str(e)}"
        }