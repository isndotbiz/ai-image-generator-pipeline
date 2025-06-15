#!/usr/bin/env python3
"""
Theme Compliance Filter
Scans THEMES block for problematic content and outputs cleansed version.
"""

import re
import yaml
import sys
from typing import List, Dict, Tuple

def load_blueprint(blueprint_path: str) -> Dict:
    """Load the content blueprint YAML file."""
    try:
        with open(blueprint_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Blueprint file {blueprint_path} not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing blueprint YAML: {e}")
        sys.exit(1)

def extract_themes_from_file(script_path: str) -> List[str]:
    """Extract THEMES block from the shell script."""
    try:
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Find the THEMES block
        themes_match = re.search(r'THEMES="([^"]+)"', content, re.DOTALL)
        if not themes_match:
            print("Error: THEMES block not found in script.")
            sys.exit(1)
        
        themes_content = themes_match.group(1)
        return [line.strip() for line in themes_content.split('\n') if line.strip()]
    except FileNotFoundError:
        print(f"Error: Script file {script_path} not found.")
        sys.exit(1)

def flag_problematic_content(themes: List[str], blueprint: Dict) -> Tuple[List[str], List[str]]:
    """Flag and identify problematic content in themes."""
    problematic_lines = []
    flagged_terms = []
    
    prohibited_terms = blueprint['prohibited_content']['findom_terms']
    
    for i, theme_line in enumerate(themes, 1):
        line_lower = theme_line.lower()
        found_terms = []
        
        for term in prohibited_terms:
            if term.lower() in line_lower:
                found_terms.append(term)
        
        if found_terms:
            problematic_lines.append(f"Line {i}: {theme_line}")
            flagged_terms.extend(found_terms)
    
    return problematic_lines, list(set(flagged_terms))

def cleanse_themes(themes: List[str], blueprint: Dict) -> List[str]:
    """Apply cleansing to themes using blueprint replacements."""
    cleansed_themes = []
    replacements = blueprint['replacement_suggestions']
    
    for theme_line in themes:
        parts = theme_line.split(' | ')
        if len(parts) >= 3:
            location, item, mantra = parts[0], parts[1], parts[2]
            slug = parts[3] if len(parts) > 3 else ""
            
            # Apply replacements to mantra
            cleansed_mantra = mantra
            for old_phrase, new_phrase in replacements.items():
                cleansed_mantra = cleansed_mantra.replace(old_phrase, new_phrase)
            
            # Reconstruct the line
            if slug:
                cleansed_line = f"{location} | {item} | {cleansed_mantra} | {slug}"
            else:
                cleansed_line = f"{location} | {item} | {cleansed_mantra}"
            
            cleansed_themes.append(cleansed_line)
        else:
            # Keep line as is if format is unexpected
            cleansed_themes.append(theme_line)
    
    return cleansed_themes

def generate_compliance_report(problematic_lines: List[str], flagged_terms: List[str]) -> str:
    """Generate a compliance report."""
    report = "\n=== THEME COMPLIANCE REPORT ===\n"
    report += f"Total problematic lines found: {len(problematic_lines)}\n"
    report += f"Flagged terms: {', '.join(flagged_terms)}\n\n"
    
    if problematic_lines:
        report += "PROBLEMATIC LINES:\n"
        for line in problematic_lines:
            report += f"  🚩 {line}\n"
        report += "\n"
    
    report += "FLAGGED TERMS ANALYSIS:\n"
    findom_terms = ['tribute', 'submit', 'surrender', 'obey', 'serve', 'worship', 'bow', 'kneel', 'revere']
    
    for term in flagged_terms:
        if term in findom_terms:
            report += f"  ❌ '{term}' - Financial domination terminology\n"
        else:
            report += f"  ⚠️  '{term}' - Power dynamic language\n"
    
    return report

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 filter_themes.py <script_path>")
        print("Example: python3 filter_themes.py gon.sh")
        sys.exit(1)
    
    script_path = sys.argv[1]
    blueprint_path = "content_blueprint.yaml"
    output_path = "themes_clean.txt"
    
    print("Loading content blueprint...")
    blueprint = load_blueprint(blueprint_path)
    
    print(f"Extracting themes from {script_path}...")
    themes = extract_themes_from_file(script_path)
    
    print(f"Analyzing {len(themes)} theme lines for compliance...")
    problematic_lines, flagged_terms = flag_problematic_content(themes, blueprint)
    
    print("Generating compliance report...")
    report = generate_compliance_report(problematic_lines, flagged_terms)
    print(report)
    
    print("Cleansing themes...")
    cleansed_themes = cleanse_themes(themes, blueprint)
    
    print(f"Writing cleansed themes to {output_path}...")
    with open(output_path, 'w') as f:
        for theme in cleansed_themes:
            f.write(f"{theme}\n")
    
    print(f"\n✅ Compliance filtering complete!")
    print(f"📄 Cleansed themes saved to: {output_path}")
    print(f"📊 Found {len(problematic_lines)} problematic lines with {len(flagged_terms)} unique flagged terms")
    
    # Save detailed report
    with open("compliance_report.txt", "w") as f:
        f.write(report)
        f.write("\nORIGINAL PROBLEMATIC THEMES:\n")
        for line in problematic_lines:
            f.write(f"{line}\n")
    
    print(f"📋 Detailed report saved to: compliance_report.txt")

if __name__ == "__main__":
    main()

