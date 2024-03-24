export async function fetchData<ReturnType>(url: string): Promise<ReturnType> {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`status code ${response.status}`);
    }
    return await response.json();
}
