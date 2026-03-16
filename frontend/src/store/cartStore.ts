/**
 * 장바구니 상태 관리 (Zustand)
 */
import { create } from 'zustand';
import { cartAPI } from '../services/api';

interface CartItem {
  item_id: number;
  product_id: string;
  product_name: string;
  specification?: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
  source: string;
  is_collected: boolean;
  added_at: string;
}

interface CartState {
  sessionId: string | null;
  items: CartItem[];
  totalPrice: number;
  itemCount: number;
  isLoading: boolean;

  fetchCart: () => Promise<void>;
  addItem: (productId: string, quantity?: number, source?: string) => Promise<boolean>;
  updateQuantity: (itemId: number, quantity: number) => Promise<void>;
  removeItem: (itemId: number) => Promise<void>;
  clearCart: () => Promise<void>;
}

export const useCartStore = create<CartState>((set) => ({
  sessionId: null,
  items: [],
  totalPrice: 0,
  itemCount: 0,
  isLoading: false,

  fetchCart: async () => {
    set({ isLoading: true });
    try {
      const res = await cartAPI.getCart();
      const data = res.data.data;
      if (data) {
        set({
          sessionId: data.session_id,
          items: data.items || [],
          totalPrice: data.total_price || 0,
          itemCount: data.item_count || 0,
        });
      }
    } catch {
      // 장바구니 없을 수 있음
    } finally {
      set({ isLoading: false });
    }
  },

  addItem: async (productId, quantity = 1, source = 'manual') => {
    try {
      await cartAPI.addItem({ product_id: productId, quantity, source });
      // 장바구니 새로고침
      const res = await cartAPI.getCart();
      const data = res.data.data;
      if (data) {
        set({
          sessionId: data.session_id,
          items: data.items || [],
          totalPrice: data.total_price || 0,
          itemCount: data.item_count || 0,
        });
      }
      return true;
    } catch {
      return false;
    }
  },

  updateQuantity: async (itemId, quantity) => {
    try {
      await cartAPI.updateItem(itemId, quantity);
      set((state) => {
        const updatedItems = state.items.map((item) =>
          item.item_id === itemId
            ? { ...item, quantity, subtotal: item.unit_price * quantity }
            : item
        );
        const newTotal = updatedItems.reduce((sum, item) => sum + (item.unit_price * item.quantity), 0);
        const newCount = updatedItems.reduce((sum, item) => sum + item.quantity, 0);
        return {
          items: updatedItems,
          totalPrice: newTotal,
          itemCount: newCount,
        };
      });
    } catch {}
  },

  removeItem: async (itemId) => {
    try {
      await cartAPI.removeItem(itemId);
      set((state) => ({
        items: state.items.filter((item) => item.item_id !== itemId),
        itemCount: state.itemCount - 1,
      }));
    } catch {}
  },

  clearCart: async () => {
    try {
      await cartAPI.clearCart();
      set({ items: [], totalPrice: 0, itemCount: 0 });
    } catch {}
  },
}));
