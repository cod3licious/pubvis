export type LoadingState = "idle" | "loading" | "loaded" | "error";

export type Article = {
    item_id: string;
    title: string;
    pub_year: number;
    publisher: string;
    authors: string;
    score?: number;
};

export type ArticleDetail = Article & {
    description: string;
    pub_date: string;
    keywords: string;
    item_url: string;
};
