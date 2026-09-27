# Ассеты лайт-новеллы

```
scenes/<scene>.jpg               фон сцены, 1920×1080
characters/<sprite>-<mood>.png   спрайт персонажа, PNG с прозрачностью
```

Имена берутся из сценариев (`content/scenarios/*.yaml`, поля `scene`
и `characters`), настроения — `calm`, `pleased`, `tense`, `upset`.

Файлов может не быть: интерфейс покажет градиент сцены и табличку с именем
персонажа. Промпты для генерации — в [`docs/08-art-prompts.md`](../../docs/08-art-prompts.md).
