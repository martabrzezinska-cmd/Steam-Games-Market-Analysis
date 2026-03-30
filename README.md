# Steam Indie Insights: Market Evolution & Recognition Analysis

**Project:** Data-Driven Analysis of Steam Games (2021-2025)  
**Author:** Marta Brzezinska
**Date:** January 7, 2026

---

## 📋 Project Overview

This project analyzes the evolution of indie games on Steam between 2021 and 2025, comparing their market presence and recognition with AAA titles.

## Dataset:

Original dataset link:
https://www.kaggle.com/datasets/jypenpen54534/steam-games-dataset-2021-2025-65k
(Access: anyone with the link can view, log in to download)

### Research Questions

1. **📈 Market Evolution** – How has the indie games market evolved compared to other games?
2. **🎮 Genre Popularity** – What types of genres are most popular among indie vs AAA games?
3. **💰 Price-to-Engagement** – How does price impact recommendations and player engagement?
4. **🏆 Awards Recognition** – Are indie games gaining more recognition in Steam Awards?

---

## 📁 Project Structure

````
project_delivery/
│
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── data_processing.ipynb              # Main analysis notebook (Jupyter)
├── streamlit_app.py                   # Interactive dashboard application
│
├── data/
│   ├── steam_data_complete.csv        # Final processed dataset (65,521 games)
│   └── steam_awards_nominees.csv      # Steam Awards data (2021-2025)

---

##  Quick Start

### 1. The data set should be already in the folder. In other case download the dataset from the link and place it in the project folder (data)


### 2. Install Dependencies

```bash
pip install -r requirements.txt
````

### 2. Run Jupyter Notebook

```bash
jupyter notebook data_processing.ipynb
```

Or open in VS Code with Jupyter extension.

### 3. Launch Interactive Dashboard

```bash
streamlit run streamlit_app.py
```

The dashboard will open in your browser at http://localhost:8501

---
