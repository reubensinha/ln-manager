export type PublishingStatus = "unknown" | "ongoing" | "completed" | "hiatus" | "stalled" | "cancelled"

export type ExternalLink = {
    name: string;
    url: string;
    icon_url?: string;
}

export type StaffRole = {
    name: string;
    role: string;
}