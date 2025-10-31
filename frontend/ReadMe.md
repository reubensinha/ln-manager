# LN-Manager - Frontend

## Adding New Features

### Creating a New Page

1. Create component in `src/pages/YourPage.tsx`
2. Add route in `App.tsx`:

```tsx
<Route path="/your-page" element={<YourPage />} />
```

3. Add navigation link in `NavbarNested.tsx`

### Adding API Endpoints

1. Add function to `src/api/api.ts`:

```typescript
export async function yourEndpoint(param: string): Promise<ResponseType> {
  const response = await api.get(`/api/v1/your-endpoint/${param}`);
  return response.data;
}
```

2. Add TypeScript types to `src/api/ApiResponse.ts`
