# Keyword Corpus Methodology
## Dil Öğrenme Uygulamaları — HCI/UX Anahtar Kelime Havuzu

**Proje:** Play Store Yorum Analizi ile HCI/UX Kelime Havuzu Genişletme
**Başlangıç tarihi:** 2026-03-28
**Araç:** Play Reviewer + extract_keywords_v2.py
**Sorumlu:** Uygar

---

## 1. Başlangıç Noktası: 471 Kelimelik Çekirdek Havuz

### 1.1 Nasıl Oluşturuldu?

Çekirdek havuz, dil öğrenme uygulamaları üzerine yapılan nitel yorum incelemesiyle oluşturulmuştur. Kelimeler doğrudan kullanıcı dilinden (verbatim) alınmış, akademik jargon değil gerçek kullanıcı ifadelerine öncelik verilmiştir.

**Kapsadığı tema kümeleri:**
| Tema | Örnek kelimeler |
|---|---|
| Geri bildirim kalitesi | `accurate feedback`, `wrong correction`, `real-time correction` |
| Teknik sorunlar | `app crashes`, `lag`, `stutters`, `recognition error` |
| AI / Konuşma | `robotic`, `human-like`, `scripted conversation` |
| Öğretmen kalitesi | `tutor unprepared`, `tutor quality varies`, `great tutor` |
| Gamification | `streak`, `hearts`, `energy system`, `XP points` |
| UX/Arayüz | `cluttered`, `intuitive`, `confusing interface` |
| Abonelik | `dark patterns`, `paywall`, `misleading pricing` |

### 1.2 Kısıtlamalar

- Tek kaynaktan, tek kişi tarafından derlendi (subjektif örnekleme riski)
- Belirli uygulamalar ağırlıklı olabilir
- Nadir ama önemli terimler eksik kalabilir

---

## 2. İlk Genişleme: Tek Ülke (v1)

### 2.1 Yöntem

**Araç:** `google-play-scraper` Python kütüphanesi
**Tarih:** 2026-03-29
**Script:** `extract_keywords.py`

**Parametreler:**
```
Dil filtresi  : İngilizce (lang="en")
Ülke          : Yalnızca ABD (country="us")
Zaman aralığı : Son 12 ay
Sıralama      : En yeni yorumdan en eskiye (NEWEST)
Max yorum     : Her uygulama için 2.000
Erken durdurma: İlk 12 ay öncesi yoruma ulaşıldığında dur
```

**9 Hedef Uygulama:**

| Uygulama | App ID | Play Store |
|---|---|---|
| Speak | com.selabs.speak | [link](https://play.google.com/store/apps/details?id=com.selabs.speak) |
| Praktika | ai.praktika.android | [link](https://play.google.com/store/apps/details?id=ai.praktika.android) |
| ELSA Speak | us.nobarriers.elsa | [link](https://play.google.com/store/apps/details?id=us.nobarriers.elsa) |
| Duolingo | com.duolingo | [link](https://play.google.com/store/apps/details?id=com.duolingo) |
| Babbel | com.babbel.mobile.android.en | [link](https://play.google.com/store/apps/details?id=com.babbel.mobile.android.en) |
| Busuu | com.busuu.android.enc | [link](https://play.google.com/store/apps/details?id=com.busuu.android.enc) |
| Cambly | com.cambly.cambly | [link](https://play.google.com/store/apps/details?id=com.cambly.cambly) |
| Preply | com.preply | [link](https://play.google.com/store/apps/details?id=com.preply) |
| HelloTalk | com.hellotalk | [link](https://play.google.com/store/apps/details?id=com.hellotalk) |

> **Not:** ELSA Speak'in ilk denemede App ID'si yanlış girildi (`us.say.elsa`). Doğru ID (`us.nobarriers.elsa`) kullanıcı tarafından Google Play'den tespit edilerek düzeltildi.

### 2.2 Sonuçlar (v1)

| Uygulama | Toplanan Yorum |
|---|---|
| Speak | 2.136 |
| Praktika | 2.050 |
| ELSA Speak | 1.742 (12 ay sınırında durdu) |
| Duolingo | 2.110 |
| Babbel | 2.078 |
| Busuu | 2.089 |
| Cambly | 57 (12 ay sınırında durdu) |
| Preply | 881 (12 ay sınırında durdu) |
| HelloTalk | 2.011 |
| **TOPLAM** | **15.154** |

> **Not:** Cambly ve Preply'nin "erken durması" bir hata değildir. Bu uygulamalar son 12 ayda ABD Google Play Store'a az yorum almıştır. Büyük olasılıkla kullanıcı tabanları iOS ağırlıklı ya da diğer ülkelerde daha aktiftir.

### 2.3 Keyword Seçim Mantığı

İki aşamalı hibrit yaklaşım kullanıldı:

**Aşama A — Kuratörlü Eşleşme:**
- HCI, UX, öğrenme deneyimi alanlarından ~250 uzman terimi önceden listelendi
- Bu terimler tüm yorumlarda arandı (regex, kelime sınırı duyarlı)
- Min. 5 görünme şartı uygulandı

**Aşama B — N-gram Çıkarımı:**
- Tüm yorumlardan 1-gram, 2-gram, 3-gram sayıldı
- Stop word filtresi uygulandı
- HCI seed kelime listesiyle örtüşme skoru hesaplandı
- Min. frekans: unigram ≥20, bigram ≥12, trigram ≥8

**Çakışma kontrolü:** Her aday kelime mevcut 471 kelimeyle karşılaştırıldı, çakışanlar çıkarıldı.

**v1 Çıktı:** 864 yeni kelime (32 curated + 832 extracted)

---

## 3. İkinci Genişleme: Zaman Penceresi Genişletme (v2)

### 3.1 Çok Ülke Hipotezinin Test Edilmesi

v1 sonuçlarında Cambly (57 yorum) ve Preply (881 yorum) az veri üretince ilk hipotez şuydu:
"Farklı ülke mağazaları farklı yorum havuzları döndürüyor olabilir."

**Empirik test yapıldı:**
```python
# Cambly için US, GB, IN mağazalarından 30'ar yorum çekildi
ids_us = {r['reviewId'] for r in batch_us}  # 30 yorum
ids_gb = {r['reviewId'] for r in batch_gb}  # 30 yorum → US ile %100 örtüşme
ids_in = {r['reviewId'] for r in batch_in}  # 30 yorum → US ile %100 örtüşme
```

**Sonuç:** `lang="en"` parametresiyle Google Play, ülkeden bağımsız aynı global İngilizce yorum havuzunu döndürmektedir. Çok ülke yaklaşımı yeni veri üretmez.

### 3.2 Gerçek Çözüm: Tek Tip Zaman Penceresi Genişletme

Tüm uygulamalarda tutarlı metodoloji için:
- Zaman penceresi 12 aydan **24 aya** çıkarıldı
- Tüm uygulamalara aynı parametre uygulandı (metodolojik tutarlılık)
- Max yorum limiti uygulama başına **3.000** olarak artırıldı

### 3.3 Parametreler (v2)

```
Dil filtresi   : İngilizce (lang="en")
Ülke           : United States (us) — diğer ülkeler aynı havuzu döndürüyor
Zaman aralığı  : Son 24 ay (tüm uygulamalar için tek tip)
Sıralama       : En yeni yorumdan en eskiye (NEWEST)
Max yorum/app  : 3.000
Script         : extract_keywords_v2.py
```

---

### 3.4 v2 Sonuçları

| Uygulama | Yorum Sayısı |
|---|---|
| Speak | 3.022 |
| Praktika | 3.019 |
| ELSA Speak | 3.139 |
| Duolingo | 3.054 |
| Babbel | 3.019 |
| Busuu | 3.112 |
| Cambly | 166 (24 ayda toplam) |
| Preply | 1.924 |
| HelloTalk | 3.020 |
| **TOPLAM** | **23.475** |

> Cambly'nin 24 ayda yalnızca 166 İngilizce Play Store yorumu olması gerçek bir veri kısıtıdır. Bu uygulama büyük ölasılıkla iOS ağırlıklı bir kullanıcı tabanına sahiptir ve/veya kullanıcıları Play Store'a yorum bırakmamaktadır.

**v2 Çıktı:** 1.202 yeni kelime (40 curated + 1.162 extracted)

---

## 4. Keyword Kalite Kontrol Kriterleri

| Kriter | Açıklama |
|---|---|
| Çakışma kontrolü | Mevcut 471 kelimeyle tam eşleşme yok |
| Minimum frekans | Curated ≥5, unigram ≥20, bigram ≥12, trigram ≥8 |
| Stop-word filtresi | Yalnızca stop-word içeren ifadeler çıkarıldı |
| İçerik kelime şartı | En az 1 adet uzunluk > 3 ve stop-word olmayan kelime |
| Jenerik ifade listesi | "language learning", "the app" gibi 25 jenerik ifade dışlandı |
| HCI ilişki skoru | N-gram adayları için seed kelime örtüşme skoru ≥1 |

---

## 5. Çıktı Dosyaları

| Dosya | İçerik |
|---|---|
| `new_keywords_hci_ux.csv` | v1 sonuçları (tek ülke) |
| `new_keywords_hci_ux.xml` | v1 sonuçları XML formatı |
| `new_keywords_hci_ux_v2.csv` | v2 sonuçları (çok ülke) + kaynak tablosu |
| `new_keywords_hci_ux_v2.xml` | v2 sonuçları + `<sources>` + `<meta>` blokları |

### CSV Yapısı (v2)
```
Bölüm 1: Analiz meta verileri (tarih, kapsam, toplam yorum)
Bölüm 2: Uygulama × ülke yorum sayısı tablosu
Bölüm 3: Yeni keyword listesi (keyword, frekans, kaynak)
```

### XML Yapısı (v2)
```xml
<keyword_analysis>
  <meta run_date="..." months="12" total_reviews="..." />
  <countries> ... </countries>
  <sources>
    <app name="..." id="..." total="..." url="..."
         United_States="..." India="..." ... />
  </sources>
  <keywords>
    <keyword freq="..." source="curated|extracted">...</keyword>
  </keywords>
</keyword_analysis>
```

---

## 6. Sınırlılıklar ve Notlar

1. **Platform kısıtı:** Yalnızca Google Play yorumları kullanıldı. App Store (iOS) yorumları dahil değil.
2. **Dil filtresi:** Yalnızca `lang="en"` parametresiyle çekildi. API dil tespiti mükemmel değildir, kısa yorumlarda hata olabilir.
3. **Yorum miktarı yanlılığı:** Duolingo gibi büyük uygulamalar orantısız katkı sağlar. Farklı ağırlıklandırma stratejileri uygulanabilir.
4. **Scraped veri zamanlaması:** Yorumlar çekme tarihinde anlık snapshot'tır. Zaman içinde değişebilir.
5. **Curated liste öznel:** HCI/UX seed terimi listesi araştırmacı tarafından oluşturuldu. Farklı araştırmacılar farklı terimler seçebilir.
6. **Frekans ≠ önem:** Sık geçen bir terim her zaman anlamlı olmayabilir; nadir ama yüksek bilgi değeri taşıyan terimler kaçabilir.

---

## 7. Yeniden Üretilebilirlik

Analizi yeniden çalıştırmak için:

```bash
# Bağımlılıkların kurulu olduğu sanal ortamdan:
cd "/Users/uygar/28 mart deneme"
.venv/bin/python3 extract_keywords_v2.py
```

Çıktılar otomatik olarak `new_keywords_hci_ux_v2.csv` ve `new_keywords_hci_ux_v2.xml` dosyalarına yazılır.

**Bağımlılıklar:** `flask`, `google-play-scraper`, `pandas` (bkz. `requirements.txt`)
