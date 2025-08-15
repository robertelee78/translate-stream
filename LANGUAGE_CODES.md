# Supported Language Codes

## Common Language Codes for Soniox

Soniox uses ISO 639-1 language codes (2-letter codes). Here are the most common ones:

### European Languages
- `en` - English
- `es` - Spanish (Español)
- `fr` - French (Français)
- `de` - German (Deutsch)
- `it` - Italian (Italiano)
- `pt` - Portuguese (Português)
- `nl` - Dutch (Nederlands)
- `el` - Greek (Ελληνικά) **[NOT gr - that's the country code!]**
- `hr` - Croatian (Hrvatski)
- `sr` - Serbian (Српски)
- `bg` - Bulgarian (Български)
- `ro` - Romanian (Română)
- `hu` - Hungarian (Magyar)
- `cs` - Czech (Čeština)
- `sk` - Slovak (Slovenčina)
- `pl` - Polish (Polski)
- `sv` - Swedish (Svenska)
- `no` - Norwegian (Norsk)
- `da` - Danish (Dansk)
- `fi` - Finnish (Suomi)

### Asian Languages  
- `zh` - Chinese (中文)
- `ja` - Japanese (日本語)
- `ko` - Korean (한국어)
- `hi` - Hindi (हिन्दी)
- `ar` - Arabic (العربية)
- `he` - Hebrew (עברית)
- `tr` - Turkish (Türkçe)
- `th` - Thai (ไทย)
- `vi` - Vietnamese (Tiếng Việt)
- `id` - Indonesian (Bahasa Indonesia)

### Other Common Languages
- `ru` - Russian (Русский)
- `uk` - Ukrainian (Українська)
- `sw` - Swahili (Kiswahili)
- `af` - Afrikaans

## Important Notes

1. **Use language codes, not country codes!**
   - ✅ `el` for Greek (language)
   - ❌ `gr` for Greek (GR is Greece country code)
   
2. **Check Soniox documentation** for supported languages
   - Not all ISO 639-1 codes may be supported
   - Some languages may have better accuracy than others

3. **Common mistakes:**
   - `gr` → use `el` for Greek
   - `jp` → use `ja` for Japanese  
   - `cn` → use `zh` for Chinese

## Configuration Examples

### English-Greek
```bash
PRIMARY_LANGUAGE=en
FOREIGN_LANGUAGE=el
```

### Spanish-Portuguese
```bash
PRIMARY_LANGUAGE=es
FOREIGN_LANGUAGE=pt
```

### German-Dutch
```bash
PRIMARY_LANGUAGE=de
FOREIGN_LANGUAGE=nl
```

## Testing Your Configuration

After updating `.env`, test with:
```bash
./translate-stream.sh -i mic -o json -t
```

Or override at runtime:
```bash
./translate-stream.sh --primary-language en --foreign-language el -i mic -o json -t
```
