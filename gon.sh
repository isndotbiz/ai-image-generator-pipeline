#!/bin/bash
set -e
# Requires: pip3 install replicate requests piexif
# Remember: export REPLICATE_API_TOKEN="YOUR_TOKEN"

# Images directory configuration
IMAGES_DIR="images"

# Ensure images directory exists
mkdir -p "$IMAGES_DIR"

# Function to generate a single image using modular helpers
gen() {
    local location="$1"
    local item="$2"
    local mantra="$3"
    local aspect_ratio="$4"
    local slug="$5"
    local platform="$6"
    local palette_id="$7"
    
    local outfile="${IMAGES_DIR}/${slug}_${palette_id}_${platform}.png"
    
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

THEMES="Maldives overwater bungalow | professional camera setup | Honor the Path to Prosperity | maldives_camera_1
Maldives overwater bungalow | silk cashmere throw | Invest Now, Thank Yourself Later | maldives_silk_2
Maldives overwater bungalow | designer watch | Answer the Call of Currency | maldives_watch_3
Maldives overwater bungalow | smart investment portfolio | Embrace Sovereign Wealth | maldives_portfolio_4
Maldives overwater bungalow | premium business card holder | Pay for Power, Stay Empowered | maldives_card_5
Maldives overwater bungalow | handcrafted Persian rug | Invest in Excellence | maldives_handcrafted_6
Maldives overwater bungalow | designer sneakers | Wealth Follows Dedication | maldives_sneaker_7
Maldives overwater bungalow | crystal wine decanter | Commit to Success | maldives_crystal_8
Maldives overwater bungalow | premium smartphone | Your Investment, Your Triumph | maldives_phone_9
Maldives overwater bungalow | touring motorcycle | Luxury Reflects Your Success | maldives_motorcycle_10
London riverside flat | professional camera setup | Build Your Capital Foundation | london_camera_11
London riverside flat | silk cashmere throw | Pursue the Yield, Earn the Life | london_silk_12
London riverside flat | designer watch | Master Balance Sheets | london_watch_13
London riverside flat | smart investment portfolio | Embrace Compounding | london_portfolio_14
London riverside flat | premium business card holder | Build Residual Income | london_card_15
London riverside flat | handcrafted Persian rug | Honor the Path to Prosperity | london_handcrafted_16
London riverside flat | designer sneakers | Invest Now, Thank Yourself Later | london_sneaker_17
London riverside flat | crystal wine decanter | Answer the Call of Currency | london_crystal_18
London riverside flat | premium smartphone | Embrace Sovereign Wealth | london_phone_19
London riverside flat | touring motorcycle | Pay for Power, Stay Empowered | london_motorcycle_20"
Paris Montmartre attic | professional camera setup | Invest in Excellence | paris_camera_21
Paris Montmartre attic | silk cashmere throw | Wealth Follows Dedication | paris_silk_22
Paris Montmartre attic | designer watch | Commit to Success | paris_watch_23
Paris Montmartre attic | smart investment portfolio | Your Investment, Your Triumph | paris_portfolio_24
Paris Montmartre attic | premium business card holder | Luxury Reflects Your Success | paris_card_25
Paris Montmartre attic | handcrafted Persian rug | Build Your Capital Foundation | paris_handcrafted_26
Paris Montmartre attic | designer sneakers | Pursue the Yield, Earn the Life | paris_sneaker_27
Paris Montmartre attic | crystal wine decanter | Master Balance Sheets | paris_crystal_28
Paris Montmartre attic | premium smartphone | Embrace Compounding | paris_phone_29
Paris Montmartre attic | touring motorcycle | Build Residual Income | paris_motorcycle_30
Santorini cliff suite | professional camera setup | Honor the Path to Prosperity | santorini_camera_31
Santorini cliff suite | silk cashmere throw | Invest Now, Thank Yourself Later | santorini_silk_32
Santorini cliff suite | designer watch | Answer the Call of Currency | santorini_watch_33
Santorini cliff suite | smart investment portfolio | Embrace Sovereign Wealth | santorini_portfolio_34
Santorini cliff suite | premium business card holder | Pay for Power, Stay Empowered | santorini_card_35
Santorini cliff suite | handcrafted Persian rug | Invest in Excellence | santorini_handcrafted_36
Santorini cliff suite | designer sneakers | Wealth Follows Dedication | santorini_sneaker_37
Santorini cliff suite | crystal wine decanter | Commit to Success | santorini_crystal_38
Santorini cliff suite | premium smartphone | Your Investment, Your Triumph | santorini_phone_39
Santorini cliff suite | touring motorcycle | Luxury Reflects Your Success | santorini_motorcycle_40
Dubai desert retreat | professional camera setup | Build Your Capital Foundation | dubai_camera_41
Dubai desert retreat | silk cashmere throw | Pursue the Yield, Earn the Life | dubai_silk_42
Dubai desert retreat | designer watch | Master Balance Sheets | dubai_watch_43
Dubai desert retreat | smart investment portfolio | Embrace Compounding | dubai_portfolio_44
Dubai desert retreat | premium business card holder | Build Residual Income | dubai_card_45
Dubai desert retreat | handcrafted Persian rug | Honor the Path to Prosperity | dubai_handcrafted_46
Dubai desert retreat | designer sneakers | Invest Now, Thank Yourself Later | dubai_sneaker_47
Dubai desert retreat | crystal wine decanter | Answer the Call of Currency | dubai_crystal_48
Dubai desert retreat | premium smartphone | Embrace Sovereign Wealth | dubai_phone_49
Dubai desert retreat | touring motorcycle | Pay for Power, Stay Empowered | dubai_motorcycle_50
Hong Kong skyline suite | professional camera setup | Invest in Excellence | hong_camera_51
Hong Kong skyline suite | silk cashmere throw | Wealth Follows Dedication | hong_silk_52
Hong Kong skyline suite | designer watch | Commit to Success | hong_watch_53
Hong Kong skyline suite | smart investment portfolio | Your Investment, Your Triumph | hong_portfolio_54
Hong Kong skyline suite | premium business card holder | Luxury Reflects Your Success | hong_card_55
Hong Kong skyline suite | handcrafted Persian rug | Build Your Capital Foundation | hong_handcrafted_56
Hong Kong skyline suite | designer sneakers | Pursue the Yield, Earn the Life | hong_sneaker_57
Hong Kong skyline suite | crystal wine decanter | Master Balance Sheets | hong_crystal_58
Hong Kong skyline suite | premium smartphone | Embrace Compounding | hong_phone_59
Hong Kong skyline suite | touring motorcycle | Build Residual Income | hong_motorcycle_60
Tuscany hilltop villa | professional camera setup | Honor the Path to Prosperity | tuscany_camera_61
Tuscany hilltop villa | silk cashmere throw | Invest Now, Thank Yourself Later | tuscany_silk_62
Tuscany hilltop villa | designer watch | Answer the Call of Currency | tuscany_watch_63
Tuscany hilltop villa | smart investment portfolio | Embrace Sovereign Wealth | tuscany_portfolio_64
Tuscany hilltop villa | premium business card holder | Pay for Power, Stay Empowered | tuscany_card_65
Tuscany hilltop villa | handcrafted Persian rug | Invest in Excellence | tuscany_handcrafted_66
Tuscany hilltop villa | designer sneakers | Wealth Follows Dedication | tuscany_sneaker_67
Tuscany hilltop villa | crystal wine decanter | Commit to Success | tuscany_crystal_68
Tuscany hilltop villa | premium smartphone | Your Investment, Your Triumph | tuscany_phone_69
Tuscany hilltop villa | touring motorcycle | Luxury Reflects Your Success | tuscany_motorcycle_70
Tokyo neon street | professional camera setup | Build Your Capital Foundation | tokyo_camera_71
Tokyo neon street | silk cashmere throw | Pursue the Yield, Earn the Life | tokyo_silk_72
Tokyo neon street | designer watch | Master Balance Sheets | tokyo_watch_73
Tokyo neon street | smart investment portfolio | Embrace Compounding | tokyo_portfolio_74
Tokyo neon street | premium business card holder | Build Residual Income | tokyo_card_75
Tokyo neon street | handcrafted Persian rug | Honor the Path to Prosperity | tokyo_handcrafted_76
Tokyo neon street | designer sneakers | Invest Now, Thank Yourself Later | tokyo_sneaker_77
Tokyo neon street | crystal wine decanter | Answer the Call of Currency | tokyo_crystal_78
Tokyo neon street | premium smartphone | Embrace Sovereign Wealth | tokyo_phone_79
Tokyo neon street | touring motorcycle | Pay for Power, Stay Empowered | tokyo_motorcycle_80
New York loft | professional camera setup | Invest in Excellence | new_camera_81
New York loft | silk cashmere throw | Wealth Follows Dedication | new_silk_82
New York loft | designer watch | Commit to Success | new_watch_83
New York loft | smart investment portfolio | Your Investment, Your Triumph | new_portfolio_84
New York loft | premium business card holder | Luxury Reflects Your Success | new_card_85
New York loft | handcrafted Persian rug | Build Your Capital Foundation | new_handcrafted_86
New York loft | designer sneakers | Pursue the Yield, Earn the Life | new_sneaker_87
New York loft | crystal wine decanter | Master Balance Sheets | new_crystal_88
New York loft | premium smartphone | Embrace Compounding | new_phone_89
New York loft | touring motorcycle | Build Residual Income | new_motorcycle_90
Monaco harbor penthouse | professional camera setup | Honor the Path to Prosperity | monaco_camera_91
Monaco harbor penthouse | silk cashmere throw | Invest Now, Thank Yourself Later | monaco_silk_92
Monaco harbor penthouse | designer watch | Answer the Call of Currency | monaco_watch_93
Monaco harbor penthouse | smart investment portfolio | Embrace Sovereign Wealth | monaco_portfolio_94
Monaco harbor penthouse | premium business card holder | Pay for Power, Stay Empowered | monaco_card_95
Monaco harbor penthouse | handcrafted Persian rug | Invest in Excellence | monaco_handcrafted_96
Monaco harbor penthouse | designer sneakers | Wealth Follows Dedication | monaco_sneaker_97
Monaco harbor penthouse | crystal wine decanter | Commit to Success | monaco_crystal_98
Monaco harbor penthouse | premium smartphone | Your Investment, Your Triumph | monaco_phone_99
Monaco harbor penthouse | touring motorcycle | Luxury Reflects Your Success | monaco_motorcycle_100
Aspen ski chalet | professional camera setup | Build Your Capital Foundation | aspen_camera_101
Aspen ski chalet | silk cashmere throw | Pursue the Yield, Earn the Life | aspen_silk_102
Aspen ski chalet | designer watch | Master Balance Sheets | aspen_watch_103
Aspen ski chalet | smart investment portfolio | Embrace Compounding | aspen_portfolio_104
Aspen ski chalet | premium business card holder | Build Residual Income | aspen_card_105
Aspen ski chalet | handcrafted Persian rug | Honor the Path to Prosperity | aspen_handcrafted_106
Aspen ski chalet | designer sneakers | Invest Now, Thank Yourself Later | aspen_sneaker_107
Aspen ski chalet | crystal wine decanter | Answer the Call of Currency | aspen_crystal_108
Aspen ski chalet | premium smartphone | Embrace Sovereign Wealth | aspen_phone_109
Aspen ski chalet | touring motorcycle | Pay for Power, Stay Empowered | aspen_motorcycle_110
Lake Como lakeside villa | professional camera setup | Invest in Excellence | como_camera_111
Lake Como lakeside villa | silk cashmere throw | Wealth Follows Dedication | como_silk_112
Lake Como lakeside villa | designer watch | Commit to Success | como_watch_113
Lake Como lakeside villa | smart investment portfolio | Your Investment, Your Triumph | como_portfolio_114
Lake Como lakeside villa | premium business card holder | Luxury Reflects Your Success | como_card_115
Lake Como lakeside villa | handcrafted Persian rug | Build Your Capital Foundation | como_handcrafted_116
Lake Como lakeside villa | designer sneakers | Pursue the Yield, Earn the Life | como_sneaker_117
Lake Como lakeside villa | crystal wine decanter | Master Balance Sheets | como_crystal_118
Lake Como lakeside villa | premium smartphone | Embrace Compounding | como_phone_119
Lake Como lakeside villa | touring motorcycle | Build Residual Income | como_motorcycle_120
Singapore Marina Bay skyloft | professional camera setup | Honor the Path to Prosperity | singapore_camera_121
Singapore Marina Bay skyloft | silk cashmere throw | Invest Now, Thank Yourself Later | singapore_silk_122
Singapore Marina Bay skyloft | designer watch | Answer the Call of Currency | singapore_watch_123
Singapore Marina Bay skyloft | smart investment portfolio | Embrace Sovereign Wealth | singapore_portfolio_124
Singapore Marina Bay skyloft | premium business card holder | Pay for Power, Stay Empowered | singapore_card_125
Singapore Marina Bay skyloft | handcrafted Persian rug | Invest in Excellence | singapore_handcrafted_126
Singapore Marina Bay skyloft | designer sneakers | Wealth Follows Dedication | singapore_sneaker_127
Singapore Marina Bay skyloft | crystal wine decanter | Commit to Success | singapore_crystal_128
Singapore Marina Bay skyloft | premium smartphone | Your Investment, Your Triumph | singapore_phone_129
Singapore Marina Bay skyloft | touring motorcycle | Luxury Reflects Your Success | singapore_motorcycle_130
Miami beachfront penthouse | professional camera setup | Build Your Capital Foundation | miami_camera_131
Miami beachfront penthouse | silk cashmere throw | Pursue the Yield, Earn the Life | miami_silk_132
Miami beachfront penthouse | designer watch | Master Balance Sheets | miami_watch_133
Miami beachfront penthouse | smart investment portfolio | Embrace Compounding | miami_portfolio_134
Miami beachfront penthouse | premium business card holder | Build Residual Income | miami_card_135
Miami beachfront penthouse | handcrafted Persian rug | Honor the Path to Prosperity | miami_handcrafted_136
Miami beachfront penthouse | designer sneakers | Invest Now, Thank Yourself Later | miami_sneaker_137
Miami beachfront penthouse | crystal wine decanter | Answer the Call of Currency | miami_crystal_138
Miami beachfront penthouse | premium smartphone | Embrace Sovereign Wealth | miami_phone_139
Miami beachfront penthouse | touring motorcycle | Pay for Power, Stay Empowered | miami_motorcycle_140
Abu Dhabi desert palace | professional camera setup | Invest in Excellence | abudhabi_camera_141
Abu Dhabi desert palace | silk cashmere throw | Wealth Follows Dedication | abudhabi_silk_142
Abu Dhabi desert palace | designer watch | Commit to Success | abudhabi_watch_143
Abu Dhabi desert palace | smart investment portfolio | Your Investment, Your Triumph | abudhabi_portfolio_144
Abu Dhabi desert palace | premium business card holder | Luxury Reflects Your Success | abudhabi_card_145
Abu Dhabi desert palace | handcrafted Persian rug | Build Your Capital Foundation | abudhabi_handcrafted_146
Abu Dhabi desert palace | designer sneakers | Pursue the Yield, Earn the Life | abudhabi_sneaker_147
Abu Dhabi desert palace | crystal wine decanter | Master Balance Sheets | abudhabi_crystal_148
Abu Dhabi desert palace | premium smartphone | Embrace Compounding | abudhabi_phone_149
Abu Dhabi desert palace | touring motorcycle | Build Residual Income | abudhabi_motorcycle_150

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


