import { render } from '@testing-library/react';
import { ErrorBoundary } from './error-boundary';
import React from 'react';

describe('ErrorBoundary', () => {
  it('renders children when no error', () => {
    const { getByText } = render(
      <ErrorBoundary>
        <div>Child</div>
      </ErrorBoundary>
    );
    expect(getByText('Child')).toBeInTheDocument();
  });
});
