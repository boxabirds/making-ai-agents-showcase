# Fixing Full-Screen Mobile Layouts: A Guide to Viewports and Safe Areas

## 1. The Problem: "It Works on My Machine!"

We developed a web application that looked pixel-perfect in desktop browser simulators (like Chrome DevTools). However, when deployed and viewed on a real iPhone, the layout was broken in several critical ways:

*   **Vertical Cropping:** The bottom of the app was cut off by the browser's bottom toolbar.
*   **Disappearing Header:** On mobile, the main header (with the hamburger menu and title) would scroll up and disappear underneath the browser's URL bar, instead of staying fixed at the top.
*   **Horizontal Cropping:** An arrow button on the far right of the screen was partially cut off.
*   **Incorrect Tray Height:** A slide-up panel (the "document viewer") that was supposed to take up 85% of the screen height was too tall, and its top was hidden.

These are classic symptoms of a layout that doesn't correctly account for the unique and dynamic nature of mobile browser viewports.

## 2. The Root Causes & The Fixes

The issues stemmed from three core misunderstandings of how mobile browsers render full-screen content.

### Cause A: The `vh` Unit is a Lie

The `vh` unit (`1vh` = 1% of the viewport height) is unreliable on mobile. Mobile browsers have a "large viewport" (when the URL bar is retracted) and a "small viewport" (when the URL bar is visible). Most browsers make `100vh` equal to the **large viewport height**.

This means on initial load, an element with `height: 100vh` is taller than the visible screen, causing its bottom to be cropped.

#### **The Fix: Use Dynamic Viewport Units (`dvh`)**

Modern CSS provides a solution: the `dvh` unit. `100dvh` always represents 100% of the *currently visible* viewport height, automatically adjusting as the browser's UI appears or disappears.

We replaced all instances of `vh` with `dvh` for our main layout containers.

```css
/* Before */
body {
  height: 100vh;
}
.app-layout {
  height: 100vh;
}

/* After */
body {
  height: 100dvh;
}
.app-layout {
  height: 100dvh;
}
```

### Cause B: Ignoring the "Notch" and Home Bar

Modern phones have physical screen obstructions like the camera notch at the top and the gesture-based home indicator at the bottom. By default, browsers keep your content within this "safe area."

To create an edge-to-edge UI, we used `viewport-fit=cover` in our viewport meta tag. This tells the browser to draw our page under the notch and home bar. However, we then become responsible for manually adding `padding` to prevent our UI from being hidden.

#### **The Fix: Use `env()` to Respect the Safe Area**

CSS provides environment variables to measure the size of these unsafe areas. We can use `env(safe-area-inset-*)` to apply the necessary padding.

We applied this padding to our edge-to-edge elements: the input bar at the bottom of the screen and the document tray that slides up from the bottom.

```css
/* For the input bar at the very bottom */
.chat-panel input-group {
  padding-bottom: env(safe-area-inset-bottom, 0);
}

/* For the slide-up document tray */
.document-viewer {
  /* max() ensures there's always some padding, even if the inset is 0 */
  padding-top: max(1rem, env(safe-area-inset-top));
}
```

### Cause C: Layout Conflicts (Grid vs. Flexbox)

Our mobile layout used a CSS Grid to create a fixed header and a content area that should fill the remaining space (`grid-template-rows: var(--header-height) 1fr;`). However, we had also given the child element inside that `1fr` track an explicit `height`. This conflict created a layout slightly taller than the screen, causing the entire page to scroll and hide the header.

Additionally, the main app container didn't have a constrained width, allowing it to render slightly wider than the screen, which caused the horizontal cropping.

#### **The Fix: Simplify and Constrain the Layout**

1.  **Remove Redundancy:** We removed the explicit `height` from the `.chat-panel` on mobile, allowing its parent grid (`1fr` row) to correctly manage its size. This stopped the unwanted vertical scrolling.

2.  **Constrain the Container:** We explicitly set the main `.app-layout` to `width: 100%` and `overflow-x: hidden`. This is a robust pattern to ensure the app never breaks out of the horizontal bounds of the screen.

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

## 3. Defensive Checklist for Future Mobile Projects

To avoid these issues in the future, follow this checklist when building full-screen mobile web experiences.

1.  **Start with the Right Meta Tag:** Always include `viewport-fit=cover` to enable edge-to-edge layouts.
    ```html
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    ```

2.  **Use Dynamic Viewport Units:** For any element that needs to be full-height, use `height: 100dvh` instead of `100vh`.

3.  **Pad for the Safe Area:** For any element that touches the edge of the screen (headers, footers, sidebars, slide-up trays), add padding to all four sides using `env()`.
    ```css
    .my-edge-to-edge-container {
      padding-top: env(safe-area-inset-top);
      padding-right: env(safe-area-inset-right);
      padding-bottom: env(safe-area-inset-bottom);
      padding-left: env(safe-area-inset-left);
    }
    ```

4.  **Constrain Your Main App Container:** Explicitly set `width: 100%` and `overflow-x: hidden` on your top-level layout container to prevent horizontal overflow.

5.  **Trust Your Layout System:** Avoid setting redundant dimensions on child elements. If a parent grid or flexbox container is designed to control an element's size, let it. Don't add a conflicting `height` or `width` on the child.

6.  **Test on Real Devices. Early and Often.** This is the most important rule. Simulators are helpful, but they cannot perfectly replicate the quirks of real-world mobile browsers and hardware.