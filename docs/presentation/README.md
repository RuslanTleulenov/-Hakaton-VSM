# Презентация проекта

`peregon.pptx` — 14 слайдов для защиты. Скриншоты в ней настоящие: сняты
с работающего стенда, а не нарисованы.

## Как пересобрать

```bash
# 1. поднять стенд с демо-данными
python backend/seed.py
python -m uvicorn app.main:app --app-dir backend --port 8040

# 2. снять экраны (нужен playwright с chromium)
python docs/presentation/shots.py docs/presentation/shots

# 3. собрать колоду (нужны node, pptxgenjs и sharp)
node docs/presentation/build.js
```

`build.js` ожидает рядом папку `shots/` со скриншотами и файлы `arch.png`,
`seq.png` — растры диаграмм из `docs/diagrams/`:

```bash
node -e "const s=require('sharp'),f=require('fs');s(f.readFileSync('docs/diagrams/components.svg')).resize({width:1800}).png().toFile('docs/presentation/arch.png')"
```

Речь к слайдам — в заметках докладчика; поминутный план демонстрации —
в [`../07-demo-script.md`](../07-demo-script.md).
