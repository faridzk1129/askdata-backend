from langchain_core.prompts import PromptTemplate, FewShotPromptTemplate

# example promt and query
examples = [
    {
        "question": "tampilkan semua data",
        "query": "SELECT * FROM data_produksi;",
    },
]

# Define an example_pmt template for create query
example_prompt = PromptTemplate.from_template(
    """`User input: {question}\nSQL Query: {query}`"""
)

# Define an answer prompt template for human answer
answer_prompt = PromptTemplate.from_template(
            """ Aturan untuk format jawaban dalam bahasa alami:
            1. Jangan pernah menampilkan kueri yang dihasilkan dalam jawaban.
            2. Jangan pernah mengeksekusi kueri yang mengandung kata-kata INSERT, UPDATE, atau DELETE.
            3. Jawablah menggunakan bahasa Indonesia.
            4. Pada bahasa alami cukup tampilkan maksimal 5 data dan beberapa kolom sebagai preview
            5. Jika nilai dari {df_to_dict_length} > 5, maka tambahkan pernyataan "Berikut adalah preview dari data yang anda inginkan, informasi lengkap mungkin tersedia pada file excel" di awal jawaban, 
            6. Jika hasil nilai dari {df_to_dict_length} <= 5, maka tampilkan pernyataan "Berikut adalah preview dari data yang anda inginkan" di awal informasi.
            7. Jika terdapat angka maka berikan pemisah titik.
            8. Bahasa alami ditampilkan dalam bentuk paragraf sehingga lebih mudah untuk dipahami
            9. Jika data yang dihasilkan merupakan hasil penjumlahan, rata-rata dan sejenisnya kamu tidak perlu menambahkan pesan bahwa data yang ditampilkan hanya preview.
            SQLResult: {result}
            Answer: """
        )