slug(text) rules:
- lowercase
- whitespace becomes a single hyphen
- drop characters other than a-z, 0-9, and hyphen
- collapse repeated hyphens
- strip leading and trailing hyphens
- empty or punctuation-only input returns ""
