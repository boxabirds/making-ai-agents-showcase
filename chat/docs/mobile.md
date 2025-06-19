
# Fixing Full-Screen Mobile Layouts: A Guide to Viewports, Safe Areas, and Input Zoom

## 1. The Problem: "It Works on My Machine!"

We developed a web application that looked pixel-perfect in desktop browser simulators (like Chrome DevTools). However, when deployed and viewed on a real iPhone, the layout was broken in several critical ways:

*   **Vertical Cropping:** The bottom of the app was cut off by the browser's bottom toolbar.
*   **Disappearing Header:** On mobile, the main header would scroll up and disappear underneath the browser's URL bar, instead of staying fixed.
*   **Horizontal Cropping:** An arrow button on the far right of the screen was partially cut off.
*   **Mangled Viewport on Keyboard Dismiss:** Tapping the text input and then closing the keyboard would leave the page in a broken, zoomed-in state, requiring a manual pinch-zoom to fix.

These are classic symptoms of a layout that doesn't correctly account for the unique and dynamic nature of mobile browser viewports.

## 2. The Root Causes & The Fixes

The issues stemmed from four core misunderstandings of how mobile browsers render full-screen content.

### Cause A: The `vh` Unit is a Lie

The `vh` unit (`1vh` = 1% of the viewport height) is unreliable on mobile. Mobile browsers have a "large viewport" (when the URL bar is retracted) and a "small viewport" (when the URL bar is visible). Most browsers make `100vh` equal to the **large viewport height**. This means on initial load, an element with `height: 100vh` is taller than the visible screen.

#### **The Fix: Use Dynamic Viewport Units (`dvh`)**

Modern CSS provides the `dvh` unit. `100dvh` always represents 100% of the *currently visible* viewport height, automatically adjusting as the browser's UI appears or disappears.

```css
/* Before */
body { height: 100vh; }

/* After */
body { height: 100dvh; }
```

### Cause B: Ignoring the "Notch" and Home Bar

To create an edge-to-edge UI, we used `viewport-fit=cover` in our meta tag. This tells the browser to draw our page under the notch and home bar, but makes us responsible for adding `padding` to keep UI elements from being hidden.

#### **The Fix: Use `env()` to Respect the Safe Area**

CSS provides environment variables to measure the size of these unsafe areas. We use `env(safe-area-inset-*)` to apply the necessary padding.

```css
/* For the input bar at the very bottom */
.chat-panel input-group {
  padding-bottom: env(safe-area-inset-bottom, 0);
}

/* For the slide-up document tray */
.document-viewer {
  /* max() ensures there's always some padding */
  padding-top: max(1rem, env(safe-area-inset-top));
}
```

### Cause C: Layout Conflicts (Grid vs. Flexbox)

Our mobile layout used a CSS Grid to create a fixed header and a content area (`grid-template-rows: var(--header-height) 1fr;`). However, we had also given the child element inside that `1fr` track an explicit `height`. This conflict created a layout slightly taller than the screen, causing the entire page to scroll.

#### **The Fix: Simplify and Constrain the Layout**

1.  **Remove Redundancy:** We removed the explicit `height` from the `.chat-panel` on mobile, allowing its parent grid to correctly manage its size.
2.  **Constrain the Container:** We set the main `.app-layout` to `width: 100%` and `overflow-x: hidden` to prevent horizontal overflow.

```css
/* In the mobile media query */
.chat-panel {
  /* We removed the `height` property from here */
}

/* On the main layout container */
.app-layout {
  width: 100%;
  overflow-x: hidden;
}
```

### Cause D: The iOS "Helpful" Auto-Zoom

This is an infamous iOS Safari quirk. If a user taps on a form input (`<input>`, `<textarea>`) and its `font-size` is **less than 16px**, Safari automatically zooms the entire page in. When the keyboard is dismissed, it often fails to zoom back out correctly, leaving the viewport mangled.

#### **The Fix: Enforce a Minimum Font Size of 16px**

The only reliable way to prevent this is to ensure the font size of the input is at least `16px` in your mobile styles. This satisfies Safari's condition, and it will not trigger the auto-zoom behavior.

```css
/* Inside the mobile media query for our input component */
.chat-input {
  /* Before: This is 15px, which triggers the zoom */
  font-size: 0.9375rem; 

  /* After: This is 16px, which prevents the zoom */
  font-size: 1rem; 
}
```

## 3. Defensive Checklist for Future Mobile Projects

To avoid these issues in the future, follow this checklist when building full-screen mobile web experiences.

1.  **Start with the Right Meta Tag:** Always include `viewport-fit=cover` to enable edge-to-edge layouts.
    ```html
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    ```

2.  **Use Dynamic Viewport Units:** For any element that needs to be full-height, use `height: 100dvh` instead of `100vh`.

3.  **Pad for the Safe Area:** For any element that touches the edge of the screen (headers, footers, sidebars), add padding using `env()`.
    ```css
    .my-edge-to-edge-container {
      padding-top: env(safe-area-inset-top);
      padding-right: env(safe-area-inset-right);
      padding-bottom: env(safe-area-inset-bottom);
      padding-left: env(safe-area-inset-left);
    }
    ```

4.  **Enforce 16px Font Size on Inputs:** For all text input fields, ensure the `font-size` is at least `16px` in your mobile styles. This prevents the dreaded iOS auto-zoom and subsequent layout mess.

5.  **Trust Your Layout System:** Avoid setting redundant dimensions on child elements. If a parent grid or flexbox container is designed to control an element's size, let it.

6.  **Constrain Your Main App Container:** Explicitly set `width: 100%` and `overflow-x: hidden` on your top-level layout container.

7.  **Test on Real Devices. Early and Often.** This is the most important rule. Simulators are helpful, but they cannot perfectly replicate the quirks of real-world mobile browsers and hardware.