Link to dataset : https://huggingface.co/datasets/staghado/ArXiv-tables

# Things to be done : 

## Preliminary analysis
- Create the database by combining all parquets = Cluster of documents 
- Replicate what they did to extract the data from tables & verification with latex_content if everything we did is correct. If not, we can modify the data 

## RAG
- choose the retireval model
- Embedding vectors for all images => the model does it 
- choose the answering model
- create the database functions to read and edit the database (similarities) => to get the most relevant documents
- create the functions to run the model
- create the functions to handle the conversation history, roles, system/user/assistant prompts
- create a basis user interface (eg. React)

## Training models 
- Find a poor quality retrieval model
- create the training data set based on the "machine learning papers"
- make the training code (fine-tuning)
- run the code
- test & benchmark

## Reports & video



