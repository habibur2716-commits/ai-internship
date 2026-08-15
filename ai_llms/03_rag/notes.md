# RAG - Basic Concepts

## RAG
RAG ka matlab hai AI ko apna document ya data provide karna, taake wo us data se jawab de sake. Waise AI sirf wohi jaanta hai jo usay training mein sikhaya gaya hai, lekin RAG se hum AI ko naya ya apna private data de sakte hain, taake AI accurate answer de.

## Chunking
Bare documents ko chhote chhote tukdon (jaise 200-500 words) mein todna, kyunke AI ki ek limit hoti hai. Jab zaroorat ho, sirf relevant chunk nikal ke AI ko diya jata hai.

## Embeddings
Text (words, sentences, paragraphs) ko numbers ki list (vector) mein convert karna. Jo words/sentences meaning mein similar hote hain, unke vectors bhi close hote hain — isse computer meaning ke hisab se data dhoond sakta hai.

## Vector Database
Ek special database jo embeddings (vectors) store karta hai, aur bohot fast dhoondh sakta hai konsa vector sabse zyada milta julta hai.

## Retrieval
User ke sawal ko bhi vector mein convert karna, phir vector database mein se sabse milte julte chunks dhoondhna.