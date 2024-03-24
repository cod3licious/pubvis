export type LoadingState = "idle" | "loading" | "loaded" | "error";
export type Article = {
    item_id: string;
    title: string;
    pub_year: number;
    publisher: string;
    authors: string;
};
