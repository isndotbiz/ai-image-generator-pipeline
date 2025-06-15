#!/bin/bash
set -e
# Requires: pip3 install replicate requests piexif
# Remember: export REPLICATE_API_TOKEN="YOUR_TOKEN"

# Function to generate a single image using modular helpers
gen() {
    local location="$1"
    local item="$2"
    local mantra="$3"
    local aspect_ratio="$4"
    local slug="$5"
    local platform="$6"
    local palette_id="$7"
    
    local outfile="${slug}_${palette_id}_${platform}.png"
    
    # Build the prompt using prompt_builder.py with palette injection
    local prompt_output=$(python3 prompt_builder.py "$location" "$item" "$mantra" "$aspect_ratio" "$palette_id")
    local prompt=$(echo "$prompt_output" | grep "^Prompt:" | sed 's/^Prompt: //')
    local negative_prompt=$(echo "$prompt_output" | grep "^Negative prompt:" | sed 's/^Negative prompt: //')
    
    # Generate the image using generate.py
    if python3 generate.py "$prompt" "$outfile" "$aspect_ratio" "$negative_prompt"; then
        # Add platform-specific watermark
        local platform_name
        case "$platform" in
            "ig") platform_name="instagram" ;;
            "tt") platform_name="tiktok" ;;
            "tw") platform_name="twitter" ;;
            *) platform_name="generic" ;;
        esac
        
        # Apply watermark using watermark.py
        local watermarked_file=$(python3 watermark.py "$outfile" "@GON" "$platform_name")
        echo "Successfully generated and watermarked: $watermarked_file"
    else
        echo "Failed to generate $outfile"
    fi
}

THEMES="Maldives overwater bungalow | vintage Leica camera | Honor the Path to Prosperity | maldives_vintage_1
Maldives overwater bungalow | silk cashmere throw | Tribute Now, Thank Yourself Later | maldives_silk_2
Maldives overwater bungalow | platinum Rolex | Obey the Call of Currency | maldives_platinum_3
Maldives overwater bungalow | gold Bitcoin coin | Surrender to Sovereign Wealth | maldives_gold_4
Maldives overwater bungalow | black Amex Centurion | Pay for Power, Stay Empowered | maldives_black_5
Maldives overwater bungalow | handcrafted Persian rug | Invest in My Indulgence | maldives_handcrafted_6
Maldives overwater bungalow | limited-edition sneaker | Wealth Follows Devotion | maldives_limited-edition_7
Maldives overwater bungalow | crystal wine decanter | Submit to Success | maldives_crystal_8
Maldives overwater bungalow | rose-gold iPhone | Your Tribute, My Triumph | maldives_rose-gold_9
Maldives overwater bungalow | electric Harley-Davidson | Luxury Earns Your Loyalty | maldives_electric_10
London riverside flat | vintage Leica camera | Claim Your Throne of Capital | london_vintage_11
London riverside flat | silk cashmere throw | Serve the Yield, Earn the Life | london_silk_12
London riverside flat | platinum Rolex | Bow to Balance Sheets | london_platinum_13
London riverside flat | gold Bitcoin coin | Kneel Before Compounding | london_gold_14
London riverside flat | black Amex Centurion | Revere Residual Income | london_black_15
London riverside flat | handcrafted Persian rug | Honor the Path to Prosperity | london_handcrafted_16
London riverside flat | limited-edition sneaker | Tribute Now, Thank Yourself Later | london_limited-edition_17
London riverside flat | crystal wine decanter | Obey the Call of Currency | london_crystal_18
London riverside flat | rose-gold iPhone | Surrender to Sovereign Wealth | london_rose-gold_19
London riverside flat | electric Harley-Davidson | Pay for Power, Stay Empowered | london_electric_20
Paris Montmartre attic | vintage Leica camera | Invest in My Indulgence | paris_vintage_21
Paris Montmartre attic | silk cashmere throw | Wealth Follows Devotion | paris_silk_22
Paris Montmartre attic | platinum Rolex | Submit to Success | paris_platinum_23
Paris Montmartre attic | gold Bitcoin coin | Your Tribute, My Triumph | paris_gold_24
Paris Montmartre attic | black Amex Centurion | Luxury Earns Your Loyalty | paris_black_25
Paris Montmartre attic | handcrafted Persian rug | Claim Your Throne of Capital | paris_handcrafted_26
Paris Montmartre attic | limited-edition sneaker | Serve the Yield, Earn the Life | paris_limited-edition_27
Paris Montmartre attic | crystal wine decanter | Bow to Balance Sheets | paris_crystal_28
Paris Montmartre attic | rose-gold iPhone | Kneel Before Compounding | paris_rose-gold_29
Paris Montmartre attic | electric Harley-Davidson | Revere Residual Income | paris_electric_30
Santorini cliff suite | vintage Leica camera | Honor the Path to Prosperity | santorini_vintage_31
Santorini cliff suite | silk cashmere throw | Tribute Now, Thank Yourself Later | santorini_silk_32
Santorini cliff suite | platinum Rolex | Obey the Call of Currency | santorini_platinum_33
Santorini cliff suite | gold Bitcoin coin | Surrender to Sovereign Wealth | santorini_gold_34
Santorini cliff suite | black Amex Centurion | Pay for Power, Stay Empowered | santorini_black_35
Santorini cliff suite | handcrafted Persian rug | Invest in My Indulgence | santorini_handcrafted_36
Santorini cliff suite | limited-edition sneaker | Wealth Follows Devotion | santorini_limited-edition_37
Santorini cliff suite | crystal wine decanter | Submit to Success | santorini_crystal_38
Santorini cliff suite | rose-gold iPhone | Your Tribute, My Triumph | santorini_rose-gold_39
Santorini cliff suite | electric Harley-Davidson | Luxury Earns Your Loyalty | santorini_electric_40
Dubai desert retreat | vintage Leica camera | Claim Your Throne of Capital | dubai_vintage_41
Dubai desert retreat | silk cashmere throw | Serve the Yield, Earn the Life | dubai_silk_42
Dubai desert retreat | platinum Rolex | Bow to Balance Sheets | dubai_platinum_43
Dubai desert retreat | gold Bitcoin coin | Kneel Before Compounding | dubai_gold_44
Dubai desert retreat | black Amex Centurion | Revere Residual Income | dubai_black_45
Dubai desert retreat | handcrafted Persian rug | Honor the Path to Prosperity | dubai_handcrafted_46
Dubai desert retreat | limited-edition sneaker | Tribute Now, Thank Yourself Later | dubai_limited-edition_47
Dubai desert retreat | crystal wine decanter | Obey the Call of Currency | dubai_crystal_48
Dubai desert retreat | rose-gold iPhone | Surrender to Sovereign Wealth | dubai_rose-gold_49
Dubai desert retreat | electric Harley-Davidson | Pay for Power, Stay Empowered | dubai_electric_50
Hong Kong skyline suite | vintage Leica camera | Invest in My Indulgence | hong_vintage_51
Hong Kong skyline suite | silk cashmere throw | Wealth Follows Devotion | hong_silk_52
Hong Kong skyline suite | platinum Rolex | Submit to Success | hong_platinum_53
Hong Kong skyline suite | gold Bitcoin coin | Your Tribute, My Triumph | hong_gold_54
Hong Kong skyline suite | black Amex Centurion | Luxury Earns Your Loyalty | hong_black_55
Hong Kong skyline suite | handcrafted Persian rug | Claim Your Throne of Capital | hong_handcrafted_56
Hong Kong skyline suite | limited-edition sneaker | Serve the Yield, Earn the Life | hong_limited-edition_57
Hong Kong skyline suite | crystal wine decanter | Bow to Balance Sheets | hong_crystal_58
Hong Kong skyline suite | rose-gold iPhone | Kneel Before Compounding | hong_rose-gold_59
Hong Kong skyline suite | electric Harley-Davidson | Revere Residual Income | hong_electric_60
Tuscany hilltop villa | vintage Leica camera | Honor the Path to Prosperity | tuscany_vintage_61
Tuscany hilltop villa | silk cashmere throw | Tribute Now, Thank Yourself Later | tuscany_silk_62
Tuscany hilltop villa | platinum Rolex | Obey the Call of Currency | tuscany_platinum_63
Tuscany hilltop villa | gold Bitcoin coin | Surrender to Sovereign Wealth | tuscany_gold_64
Tuscany hilltop villa | black Amex Centurion | Pay for Power, Stay Empowered | tuscany_black_65
Tuscany hilltop villa | handcrafted Persian rug | Invest in My Indulgence | tuscany_handcrafted_66
Tuscany hilltop villa | limited-edition sneaker | Wealth Follows Devotion | tuscany_limited-edition_67
Tuscany hilltop villa | crystal wine decanter | Submit to Success | tuscany_crystal_68
Tuscany hilltop villa | rose-gold iPhone | Your Tribute, My Triumph | tuscany_rose-gold_69
Tuscany hilltop villa | electric Harley-Davidson | Luxury Earns Your Loyalty | tuscany_electric_70
Tokyo neon street | vintage Leica camera | Claim Your Throne of Capital | tokyo_vintage_71
Tokyo neon street | silk cashmere throw | Serve the Yield, Earn the Life | tokyo_silk_72
Tokyo neon street | platinum Rolex | Bow to Balance Sheets | tokyo_platinum_73
Tokyo neon street | gold Bitcoin coin | Kneel Before Compounding | tokyo_gold_74
Tokyo neon street | black Amex Centurion | Revere Residual Income | tokyo_black_75
Tokyo neon street | handcrafted Persian rug | Honor the Path to Prosperity | tokyo_handcrafted_76
Tokyo neon street | limited-edition sneaker | Tribute Now, Thank Yourself Later | tokyo_limited-edition_77
Tokyo neon street | crystal wine decanter | Obey the Call of Currency | tokyo_crystal_78
Tokyo neon street | rose-gold iPhone | Surrender to Sovereign Wealth | tokyo_rose-gold_79
Tokyo neon street | electric Harley-Davidson | Pay for Power, Stay Empowered | tokyo_electric_80
New York loft | vintage Leica camera | Invest in My Indulgence | new_vintage_81
New York loft | silk cashmere throw | Wealth Follows Devotion | new_silk_82
New York loft | platinum Rolex | Submit to Success | new_platinum_83
New York loft | gold Bitcoin coin | Your Tribute, My Triumph | new_gold_84
New York loft | black Amex Centurion | Luxury Earns Your Loyalty | new_black_85
New York loft | handcrafted Persian rug | Claim Your Throne of Capital | new_handcrafted_86
New York loft | limited-edition sneaker | Serve the Yield, Earn the Life | new_limited-edition_87
New York loft | crystal wine decanter | Bow to Balance Sheets | new_crystal_88
New York loft | rose-gold iPhone | Kneel Before Compounding | new_rose-gold_89
New York loft | electric Harley-Davidson | Revere Residual Income | new_electric_90
Monaco harbor penthouse | vintage Leica camera | Honor the Path to Prosperity | monaco_vintage_91
Monaco harbor penthouse | silk cashmere throw | Tribute Now, Thank Yourself Later | monaco_silk_92
Monaco harbor penthouse | platinum Rolex | Obey the Call of Currency | monaco_platinum_93
Monaco harbor penthouse | gold Bitcoin coin | Surrender to Sovereign Wealth | monaco_gold_94
Monaco harbor penthouse | black Amex Centurion | Pay for Power, Stay Empowered | monaco_black_95
Monaco harbor penthouse | handcrafted Persian rug | Invest in My Indulgence | monaco_handcrafted_96
Monaco harbor penthouse | limited-edition sneaker | Wealth Follows Devotion | monaco_limited-edition_97
Monaco harbor penthouse | crystal wine decanter | Submit to Success | monaco_crystal_98
Monaco harbor penthouse | rose-gold iPhone | Your Tribute, My Triumph | monaco_rose-gold_99
Monaco harbor penthouse | electric Harley-Davidson | Luxury Earns Your Loyalty | monaco_electric_100
Aspen ski chalet | vintage Leica camera | Claim Your Throne of Capital | aspen_vintage_101
Aspen ski chalet | silk cashmere throw | Serve the Yield, Earn the Life | aspen_silk_102
Aspen ski chalet | platinum Rolex | Bow to Balance Sheets | aspen_platinum_103
Aspen ski chalet | gold Bitcoin coin | Kneel Before Compounding | aspen_gold_104
Aspen ski chalet | black Amex Centurion | Revere Residual Income | aspen_black_105
Aspen ski chalet | handcrafted Persian rug | Honor the Path to Prosperity | aspen_handcrafted_106
Aspen ski chalet | limited-edition sneaker | Tribute Now, Thank Yourself Later | aspen_limited-edition_107
Aspen ski chalet | crystal wine decanter | Obey the Call of Currency | aspen_crystal_108
Aspen ski chalet | rose-gold iPhone | Surrender to Sovereign Wealth | aspen_rose-gold_109
Aspen ski chalet | electric Harley-Davidson | Pay for Power, Stay Empowered | aspen_electric_110
Lake Como lakeside villa | vintage Leica camera | Invest in My Indulgence | como_vintage_111
Lake Como lakeside villa | silk cashmere throw | Wealth Follows Devotion | como_silk_112
Lake Como lakeside villa | platinum Rolex | Submit to Success | como_platinum_113
Lake Como lakeside villa | gold Bitcoin coin | Your Tribute, My Triumph | como_gold_114
Lake Como lakeside villa | black Amex Centurion | Luxury Earns Your Loyalty | como_black_115
Lake Como lakeside villa | handcrafted Persian rug | Claim Your Throne of Capital | como_handcrafted_116
Lake Como lakeside villa | limited-edition sneaker | Serve the Yield, Earn the Life | como_limited-edition_117
Lake Como lakeside villa | crystal wine decanter | Bow to Balance Sheets | como_crystal_118
Lake Como lakeside villa | rose-gold iPhone | Kneel Before Compounding | como_rose-gold_119
Lake Como lakeside villa | electric Harley-Davidson | Revere Residual Income | como_electric_120
Singapore Marina Bay skyloft | vintage Leica camera | Honor the Path to Prosperity | singapore_vintage_121
Singapore Marina Bay skyloft | silk cashmere throw | Tribute Now, Thank Yourself Later | singapore_silk_122
Singapore Marina Bay skyloft | platinum Rolex | Obey the Call of Currency | singapore_platinum_123
Singapore Marina Bay skyloft | gold Bitcoin coin | Surrender to Sovereign Wealth | singapore_gold_124
Singapore Marina Bay skyloft | black Amex Centurion | Pay for Power, Stay Empowered | singapore_black_125
Singapore Marina Bay skyloft | handcrafted Persian rug | Invest in My Indulgence | singapore_handcrafted_126
Singapore Marina Bay skyloft | limited-edition sneaker | Wealth Follows Devotion | singapore_limited-edition_127
Singapore Marina Bay skyloft | crystal wine decanter | Submit to Success | singapore_crystal_128
Singapore Marina Bay skyloft | rose-gold iPhone | Your Tribute, My Triumph | singapore_rose-gold_129
Singapore Marina Bay skyloft | electric Harley-Davidson | Luxury Earns Your Loyalty | singapore_electric_130
Miami beachfront penthouse | vintage Leica camera | Claim Your Throne of Capital | miami_vintage_131
Miami beachfront penthouse | silk cashmere throw | Serve the Yield, Earn the Life | miami_silk_132
Miami beachfront penthouse | platinum Rolex | Bow to Balance Sheets | miami_platinum_133
Miami beachfront penthouse | gold Bitcoin coin | Kneel Before Compounding | miami_gold_134
Miami beachfront penthouse | black Amex Centurion | Revere Residual Income | miami_black_135
Miami beachfront penthouse | handcrafted Persian rug | Honor the Path to Prosperity | miami_handcrafted_136
Miami beachfront penthouse | limited-edition sneaker | Tribute Now, Thank Yourself Later | miami_limited-edition_137
Miami beachfront penthouse | crystal wine decanter | Obey the Call of Currency | miami_crystal_138
Miami beachfront penthouse | rose-gold iPhone | Surrender to Sovereign Wealth | miami_rose-gold_139
Miami beachfront penthouse | electric Harley-Davidson | Pay for Power, Stay Empowered | miami_electric_140
Abu Dhabi desert palace | vintage Leica camera | Invest in My Indulgence | abudhabi_vintage_141
Abu Dhabi desert palace | silk cashmere throw | Wealth Follows Devotion | abudhabi_silk_142
Abu Dhabi desert palace | platinum Rolex | Submit to Success | abudhabi_platinum_143
Abu Dhabi desert palace | gold Bitcoin coin | Your Tribute, My Triumph | abudhabi_gold_144
Abu Dhabi desert palace | black Amex Centurion | Luxury Earns Your Loyalty | abudhabi_black_145
Abu Dhabi desert palace | handcrafted Persian rug | Claim Your Throne of Capital | abudhabi_handcrafted_146
Abu Dhabi desert palace | limited-edition sneaker | Serve the Yield, Earn the Life | abudhabi_limited-edition_147
Abu Dhabi desert palace | crystal wine decanter | Bow to Balance Sheets | abudhabi_crystal_148
Abu Dhabi desert palace | rose-gold iPhone | Kneel Before Compounding | abudhabi_rose-gold_149
Abu Dhabi desert palace | electric Harley-Davidson | Revere Residual Income | abudhabi_electric_150"

while IFS='|' read -r location item mantra slug; do
  [ -z "$location" ]  continue
  location=$(echo "$location" | xargs)
  item=$(echo "$item" | xargs)
  mantra=$(echo "$mantra" | xargs)
  slug=$(echo "$slug" | xargs)
  
  # Generate for each palette (A and B)
  for palette in A B; do
    # Generate for each platform with appropriate aspect ratios
    gen "$location" "$item" "$mantra" "4:5"  "$slug" "ig" "$palette"
    gen "$location" "$item" "$mantra" "9:16" "$slug" "tt" "$palette"
    gen "$location" "$item" "$mantra" "16:9" "$slug" "tw" "$palette"
  done
done <<< "$THEMES"

echo "All images rendered."


