import type { VueCookies } from "vue-cookies";

export async function fetchData<ReturnType>(url: string): Promise<ReturnType> {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`status code ${response.status}`);
    }
    return await response.json();
}

export function getOrSetUserIdCookie(cookies: VueCookies): string {
    const userId = cookies.get("userId");
    if (!userId) {
        const randomUserId = generateRandomUserId();
        cookies.set("userId", randomUserId, "5y");
        return randomUserId;
    }
    return userId;
}

function generateRandomUserId() {
    const timestamp = Date.now().toString();
    const randomString = Math.random().toString(36).substring(2, 15);
    return `${timestamp}-${randomString}`;
}
