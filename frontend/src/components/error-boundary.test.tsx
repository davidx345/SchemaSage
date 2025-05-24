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

  it('catches and displays error from child', () => {
    // Component that throws
    const Problem = () => { throw new Error('Boom!'); };
    const { getByText } = render(
      <ErrorBoundary>
        <Problem />
      </ErrorBoundary>
    );
    expect(getByText('Something went wrong')).toBeInTheDocument();
    expect(getByText('Boom!')).toBeInTheDocument();
  });
});
