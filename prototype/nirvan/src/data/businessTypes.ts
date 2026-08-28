import type { BusinessTypeDef } from "../types";

export const businessTypes: BusinessTypeDef[] = [
  // SHOP
  { id: "jewelry", category: "shop", name: "Jewelry Shop", description: "Retail of gold, silver & precious stone jewellery", icon: "Gem" },
  { id: "hotel", category: "shop", name: "Hotel", description: "Lodging, hospitality & food service establishment", icon: "BedDouble" },
  { id: "general-store", category: "shop", name: "General Store", description: "Retail of everyday consumer goods", icon: "ShoppingBasket" },
  { id: "medical-store", category: "shop", name: "Medical Store", description: "Retail sale of drugs & pharmaceutical products", icon: "Pill" },
  // INDUSTRY
  { id: "food", category: "industry", name: "Food Processing", description: "Manufacturing & processing of food products", icon: "Wheat" },
  { id: "textile", category: "industry", name: "Textile", description: "Spinning, weaving, dyeing & garment manufacturing", icon: "Shirt" },
  { id: "metal", category: "industry", name: "Metal & Engineering", description: "Metal fabrication, foundry & engineering works", icon: "Hammer" },
  { id: "sugar", category: "industry", name: "Sugar Industry", description: "Sugarcane crushing & sugar manufacturing", icon: "Factory" },
];

export const indianStates = [
  "Maharashtra", "Karnataka", "Gujarat", "Tamil Nadu", "Uttar Pradesh", "Punjab", "Rajasthan", "Madhya Pradesh",
];

export const districtsByState: Record<string, string[]> = {
  Maharashtra: ["Pune", "Nashik", "Nagpur", "Mumbai Suburban", "Aurangabad"],
  Karnataka: ["Mysuru", "Bengaluru Urban", "Belagavi", "Hubballi-Dharwad"],
  Gujarat: ["Ahmedabad", "Surat", "Vadodara", "Rajkot"],
  "Tamil Nadu": ["Coimbatore", "Chennai", "Madurai", "Salem"],
  "Uttar Pradesh": ["Noida", "Kanpur", "Lucknow", "Agra"],
  Punjab: ["Ludhiana", "Amritsar", "Jalandhar"],
  Rajasthan: ["Jaipur", "Jodhpur", "Udaipur"],
  "Madhya Pradesh": ["Indore", "Bhopal", "Gwalior"],
};
