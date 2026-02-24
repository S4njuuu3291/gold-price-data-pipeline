## TECHNICAL DESIGN DOCUMENT

### Project Overview & Goals

Project ini bertujuan untuk mengembangkan sistem otomatis untuk reminder pembelian emas berdasarkan strategi Dollar Cost Averaging (DCA). Sistem ini akan memantau harga emas secara otomatis dan memberikan sinyal ke Whatsapp pengguna ketika:
1. Setiap tanggal 15 setiap bulan
2. Harga saat ini at least lebih kecil 2% dari rata-rata harga mingguan.

Selain itu, karena pipeline data sekaligus menyimpan data harga emas, maka sistem ini juga dapat digunakan untuk keperluan analisis harga emas di masa depan.

---

### System Architecture

![System Architecture](img/system-architecture.png)

---

### Data Schema and Medallion Layering

#### Bronze Layer
```json
{
  "name": "Gold",
  "price": 5172.299805,
  "symbol": "XAU",
  "updatedAt": "2026-02-24T07:01:40Z",
  "updatedAtReadable": "a few seconds ago"
}
```

#### Silver Layer
```sql
CREATE OR REPLACE TABLE silver_gold_price AS
SELECT
  name,
  price,
  symbol,
  TIMESTAMP(updatedAt) AS updated_at
FROM bronze_gold_price;
```
---

### Alerting Logic
Sistem akan memberikan sinyal beli ketika harga saat ini lebih kecil 2% dari rata-rata harga mingguan. Secara matematis, kondisi untuk alert adalah:

$$Price < (Weekly\_Avg \times 0.98)$$

### Cost Estimation
- Estimasi eksekusi per bulan adalah sekitar: 
$(4 \text{ kali per jam} \times 24 \text{ jam} \times 30 \text{ hari}) = 2.880$ eksekusi per Cloud Function. 
- Jumlah ini masih jauh di bawah batas Free Tier GCP
- Total cost = $0
---




